"""Procurement service — business logic layer (Maker Agent).

Rules (docs/agents/BACKEND_AGENTS.md):
- Does NOT import AsyncSession — only repository interfaces.
- Orchestrates repository calls and Langflow Maker Agent.
- NEVER log API keys or tokens (docs/SECURITY.md).
"""

from __future__ import annotations

import json
import re
import statistics
import time
import uuid
from decimal import Decimal

import httpx
import structlog

from timbang.modules.procurement.repository import PriceQuoteRepository, VendorRepository
from timbang.modules.procurement.schemas import (
    PriceQuoteCreate,
    PriceQuoteRead,
    PriceValidationResult,
    RecommendationResponse,
    VendorCreate,
    VendorRead,
)
from timbang.shared.core.config import get_settings
from timbang.shared.core.exceptions import (
    DomainError,
    NotFoundError,
    UpstreamError,
    ValidationError,
)

log = structlog.get_logger(__name__)

_OUTLIER_THRESHOLD = Decimal("0.30")  # 30% deviation from median

# Regex to strip markdown code fences: ```json ... ``` or ``` ... ```
_MARKDOWN_FENCE_RE = re.compile(r"```(?:json)?\s*(.+?)\s*```", re.DOTALL)


# ── Langflow helpers ──────────────────────────────────────────────────────────


def _extract_chat_text(data: dict) -> str:
    """Defensively extract the chat text from a Langflow response payload.

    Tries the canonical path first, then falls back to a recursive search
    for the first non-empty "text" value in the response tree.
    """
    # Canonical Langflow chat output path
    try:
        return str(data["outputs"][0]["outputs"][0]["results"]["message"]["text"])
    except (KeyError, IndexError, TypeError):
        pass

    # Fallback: walk the nested structure looking for a "text" key
    def _search(obj: object) -> str | None:
        if isinstance(obj, dict):
            if "text" in obj and isinstance(obj["text"], str) and obj["text"].strip():
                return obj["text"]
            for v in obj.values():
                found = _search(v)
                if found:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = _search(item)
                if found:
                    return found
        return None

    text = _search(data)
    if text:
        return text

    # Last resort: return the raw JSON as a string
    return json.dumps(data, ensure_ascii=False)


def _try_parse_json(text: str) -> dict | None:
    """Try to parse text as JSON. Strips markdown fences if present.

    Returns the parsed dict, or None if parsing fails in all attempts.
    """
    # Attempt 1: direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Attempt 2: strip markdown code fence then parse
    match = _MARKDOWN_FENCE_RE.search(text)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _build_response(parsed: dict) -> RecommendationResponse:
    """Build a RecommendationResponse from a parsed Langflow JSON dict.

    Handles both the new structured format (vendor_name + items[]) and the
    legacy format (vendor_id + reason + estimated_saving) gracefully.
    """
    return RecommendationResponse.model_validate(parsed)


class ProcurementService:
    """Business logic for the Maker Agent procurement context."""

    def __init__(
        self,
        vendor_repo: VendorRepository,
        quote_repo: PriceQuoteRepository,
    ) -> None:
        self._vendor_repo = vendor_repo
        self._quote_repo = quote_repo

    # ── Vendors ──────────────────────────────────────────────────────────────

    async def list_vendors(self, limit: int = 50) -> list[VendorRead]:
        """Return a list of all vendors."""
        vendors = await self._vendor_repo.list(limit=limit)
        return [VendorRead.model_validate(v) for v in vendors]

    async def register_vendor(self, data: VendorCreate) -> VendorRead:
        """Register a new vendor. Raises ValidationError if name already exists."""
        existing = await self._vendor_repo.get_by_name(data.name)
        if existing is not None:
            raise ValidationError(f"Vendor with name '{data.name}' already exists.")
        vendor = await self._vendor_repo.create(data)
        log.info("vendor_registered", vendor_id=str(vendor.id), name=vendor.name)
        return VendorRead.model_validate(vendor)

    # ── Quotes ───────────────────────────────────────────────────────────────

    async def submit_quote(self, vendor_id: uuid.UUID, data: PriceQuoteCreate) -> PriceQuoteRead:
        """Submit a price quote for a vendor. Raises NotFoundError if vendor missing."""
        vendor = await self._vendor_repo.get(vendor_id)
        if vendor is None:
            raise NotFoundError(f"Vendor {vendor_id} not found.")
        # Ensure vendor_id on data matches path param
        data_dict = data.model_dump()
        data_dict["vendor_id"] = vendor_id
        quote = await self._quote_repo.create(PriceQuoteCreate(**data_dict))
        log.info("quote_submitted", quote_id=str(quote.id), item=quote.item_name)
        return PriceQuoteRead.model_validate(quote)

    # ── Cross-validation ─────────────────────────────────────────────────────

    async def cross_validate_price(
        self, item_name: str, quotes: list[PriceQuoteRead] | None = None
    ) -> PriceValidationResult:
        """Calculate median price and flag outliers.

        Requires at least 2 quotes. Outlier threshold: |price-median|/median > 30%.
        """
        if quotes is None:
            db_quotes = await self._quote_repo.list_by_item(item_name)
            quotes = [PriceQuoteRead.model_validate(q) for q in db_quotes]

        if len(quotes) < 2:
            raise ValidationError(
                f"Cross-validation requires at least 2 quotes for '{item_name}', "
                f"got {len(quotes)}."
            )

        prices = [float(q.price) for q in quotes]
        median_f = statistics.median(prices)
        median = Decimal(str(median_f))
        min_price = Decimal(str(min(prices)))
        max_price = Decimal(str(max(prices)))
        spread = (max_price - min_price) / median * 100 if median else Decimal("0")

        flagged: list[uuid.UUID] = []
        for q in quotes:
            deviation = abs(q.price - median) / median if median else Decimal("0")
            if deviation > _OUTLIER_THRESHOLD:
                flagged.append(q.vendor_id)

        return PriceValidationResult(
            median=median,
            min=min_price,
            max=max_price,
            flagged_vendor_ids=flagged,
            spread_percent=spread.quantize(Decimal("0.01")),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _load_quotes_for_item(self, item_name: str) -> list[PriceQuoteRead]:
        """Load and validate quotes from the repository for a given item."""
        db_quotes = await self._quote_repo.list_by_item(item_name)
        return [PriceQuoteRead.model_validate(q) for q in db_quotes]

    # ── Recommendation (Langflow Maker Agent) ─────────────────────────────────

    async def get_recommendation(
        self,
        item_name: str,
        quotes: list[PriceQuoteRead] | None = None,
    ) -> RecommendationResponse:
        """Call Langflow Maker Agent to recommend the best vendor for an item.

        Raises UpstreamError on timeout, non-200 response, or missing config.
        NEVER logs api_key.
        """
        settings = get_settings()

        # 1. Guard: flow ID must be configured
        if not settings.langflow_maker_flow_id:
            raise UpstreamError(
                "LANGFLOW_MAKER_FLOW_ID belum dikonfigurasi. "
                "Set env var LANGFLOW_MAKER_FLOW_ID sebelum menggunakan endpoint ini."
            )

        # 2. Load quotes from DB if not supplied
        if quotes is None:
            quotes = await self._load_quotes_for_item(item_name)

        if not quotes:
            raise DomainError(f"No price quotes found for item '{item_name}'.")

        # 3. Build prompt
        quotes_payload = [q.model_dump(mode="json") for q in quotes]
        prompt = (
            "Ekstrak data penawaran vendor, bandingkan harga dengan harga pasar "
            "terkini, dan berikan rekomendasi lengkap dengan sumber URL.\n\n"
            f"Item yang dianalisis: {item_name}\n"
            f"Data quote vendor: {json.dumps(quotes_payload, ensure_ascii=False)}"
        )

        # 4. Call Langflow
        url = f"{settings.langflow_base_url}/api/v1/run/{settings.langflow_maker_flow_id}"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.langflow_api_key:
            headers["x-api-key"] = settings.langflow_api_key  # only if configured

        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=settings.langflow_timeout_seconds) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json={
                        "input_value": prompt,
                        "input_type": "chat",
                        "output_type": "chat",
                    },
                )
        except httpx.TimeoutException as exc:
            raise UpstreamError(f"Langflow request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(f"Langflow HTTP error: {exc}") from exc

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        log.info(
            "langflow_maker_called",
            flow_id=settings.langflow_maker_flow_id,
            item_name=item_name,
            status_code=resp.status_code,
            elapsed_ms=elapsed_ms,
            # api_key intentionally NOT logged
        )

        # 5. Check status
        if resp.status_code != 200:
            raise UpstreamError(f"Langflow returned HTTP {resp.status_code}: {resp.text[:300]}")

        # 6. Extract chat text from Langflow response envelope
        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise UpstreamError(f"Langflow response is not valid JSON: {exc}") from exc

        text = _extract_chat_text(data)

        # 7. Parse text as structured JSON (handles plain JSON and markdown fences)
        parsed = _try_parse_json(text)
        if parsed is not None:
            try:
                return _build_response(parsed)
            except Exception:  # noqa: BLE001 — validation errors from Pydantic
                pass

        # 8. Fallback: wrap raw text (e.g. purely natural-language LLM output)
        return RecommendationResponse(raw_text=text, reason=text)

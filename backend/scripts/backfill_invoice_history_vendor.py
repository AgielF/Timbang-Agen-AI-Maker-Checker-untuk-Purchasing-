#!/usr/bin/env python3
"""Backfill vendor_reference for INVOICE_HISTORY records that have empty vendor_reference.

This script finds all audit_findings with evidence_type='INVOICE_HISTORY' and empty
vendor_reference, then looks up the corresponding PO record (same transaction_id)
to get the vendor's NPWP and updates the invoice history record.
"""

import asyncio
import sys
from decimal import Decimal

from sqlalchemy import select, update

from timbang.modules.audit.models import AuditFinding
from timbang.shared.db.base import Base
from timbang.shared.db.session import engine, async_session_factory as session_factory


async def backfill_invoice_history_vendor() -> int:
    """Backfill vendor_reference for INVOICE_HISTORY records.

    Returns:
        Number of records updated.
    """
    async with session_factory() as session:
        # Find all INVOICE_HISTORY records with empty vendor_reference
        stmt = select(AuditFinding).where(
            AuditFinding.evidence_type == "INVOICE_HISTORY",
            AuditFinding.vendor_reference == "",
        )
        result = await session.execute(stmt)
        invoice_histories = list(result.scalars().all())

        if not invoice_histories:
            print("No INVOICE_HISTORY records with empty vendor_reference found.")
            return 0

        print(f"Found {len(invoice_histories)} INVOICE_HISTORY records to backfill.")

        updated_count = 0
        for invoice_hist in invoice_histories:
            # Look for a PO_HISTORY or other record with same transaction_id that has vendor_reference
            stmt_po = select(AuditFinding).where(
                AuditFinding.transaction_id == invoice_hist.transaction_id,
                AuditFinding.vendor_reference != "",
            ).limit(1)
            result_po = await session.execute(stmt_po)
            po_record = result_po.scalar_one_or_none()

            if po_record and po_record.vendor_reference:
                # Update the invoice history record
                update_stmt = (
                    update(AuditFinding)
                    .where(AuditFinding.id == invoice_hist.id)
                    .values(vendor_reference=po_record.vendor_reference)
                )
                await session.execute(update_stmt)
                updated_count += 1
                print(
                    f"Updated invoice history {invoice_hist.po_number} "
                    f"(txn: {invoice_hist.transaction_id[:8]}...) "
                    f"with vendor_reference={po_record.vendor_reference}"
                )
            else:
                print(
                    f"WARNING: Could not find vendor for invoice history "
                    f"{invoice_hist.po_number} (txn: {invoice_hist.transaction_id[:8]}...)"
                )

        await session.commit()
        print(f"Backfill complete. Updated {updated_count} records.")
        return updated_count


if __name__ == "__main__":
    try:
        count = asyncio.run(backfill_invoice_history_vendor())
        sys.exit(0 if count >= 0 else 1)
    except Exception as e:
        print(f"Error during backfill: {e}")
        sys.exit(1)
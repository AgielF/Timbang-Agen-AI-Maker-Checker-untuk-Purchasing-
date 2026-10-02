import { memo } from 'react';
import Text from '../atoms/Text';
import Badge from '../atoms/Badge';
import Button from '../atoms/Button';

const fmtIDR = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  maximumFractionDigits: 0,
});

/**
 * RecommendationCard — success result card for Maker page.
 * Props:
 *   result     {Object} RecommendationResponse
 *   onValidate {Function}
 */
function RecommendationCard({ result = {}, onValidate }) {
  const primaryItem = result.items?.[0] ?? {};
  const vendorName  = result.vendor_name ?? primaryItem.recommended_vendor ?? '—';
  const price       = primaryItem.quoted_price ?? 0;
  const reason      = result.reason ?? result.raw_text ?? '';
  const confidence  = typeof result.confidence === 'number' ? result.confidence : null;

  return (
    <article className="border border-[var(--border-light)] bg-white p-6 flex flex-col gap-5">
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <Text as="h2" variant="h2" className="text-ink leading-tight">
          {vendorName}
        </Text>
        <Badge variant="success" className="shrink-0 mt-1">Recommendation Ready</Badge>
      </div>

      {/* Price */}
      <div className="flex flex-col gap-0.5">
        <span className="text-xs text-[var(--color-text-mute)] uppercase tracking-wider">Harga yang Direkomendasikan</span>
        <span className="font-mono tabular-nums text-3xl font-bold text-ink">
          {fmtIDR.format(price)}
        </span>
      </div>

      {/* Reasoning */}
      {reason && (
        <div className="flex flex-col gap-1">
          <span className="text-xs text-[var(--color-text-mute)] uppercase tracking-wider">Reasoning</span>
          <p className="text-sm text-ink leading-relaxed">{reason}</p>
        </div>
      )}

      {/* Confidence bar */}
      {confidence !== null && (
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between items-center">
            <span className="text-xs text-[var(--color-text-mute)] uppercase tracking-wider">Confidence</span>
            <span className="text-xs font-mono tabular-nums text-ink">
              {Math.round(confidence * 100)}%
            </span>
          </div>
          <div className="h-1.5 w-full bg-ink/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-electric rounded-full transition-all"
              style={{ width: `${Math.min(100, Math.round(confidence * 100))}%` }}
            />
          </div>
        </div>
      )}

      {/* CTA */}
      {onValidate && (
        <Button variant="ghost" size="sm" className="self-start" onClick={onValidate}>
          Validate this price
        </Button>
      )}
    </article>
  );
}

export default memo(RecommendationCard);

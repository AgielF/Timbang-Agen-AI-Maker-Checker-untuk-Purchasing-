import { memo } from 'react';
import Badge from '../atoms/Badge';

function FeatureCell({ title, caption, comingSoon = false }) {
  return (
    <div className="flex flex-col gap-2 p-6 border border-[var(--border-light)]">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-base font-semibold text-ink">{title}</span>
        {comingSoon && (
          <Badge variant="warning" size="sm">Coming Soon</Badge>
        )}
      </div>
      {caption && (
        <p className="text-sm text-[var(--color-text-mute)] leading-relaxed">
          {caption}
        </p>
      )}
    </div>
  );
}

export default memo(FeatureCell);

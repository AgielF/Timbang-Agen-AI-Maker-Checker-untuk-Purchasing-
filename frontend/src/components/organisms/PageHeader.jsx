import { memo } from 'react';
import Text from '../atoms/Text';
import Badge from '../atoms/Badge';

/**
 * PageHeader — section header for app pages.
 * Props:
 *   title    {string}  required — page title (h2)
 *   subtitle {string}  optional — descriptive subtitle
 *   badge    {{ label: string, variant: string }} optional — badge on the right
 */
function PageHeader({ title, subtitle, badge }) {
  return (
    <header className="flex items-start justify-between border-b border-[var(--border-light)] pb-6 mb-8">
      <div className="flex flex-col gap-1">
        <Text as="h2" variant="h2" className="text-ink">
          {title}
        </Text>
        {subtitle && (
          <Text variant="caption">
            {subtitle}
          </Text>
        )}
      </div>

      {badge && (
        <Badge variant={badge.variant ?? 'default'} className="mt-1 shrink-0">
          {badge.label}
        </Badge>
      )}
    </header>
  );
}

export default memo(PageHeader);

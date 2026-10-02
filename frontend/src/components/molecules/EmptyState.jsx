import { memo } from 'react';
import Icon from '../atoms/Icon';
import Text from '../atoms/Text';
import Button from '../atoms/Button';

function EmptyState({
  icon = 'file-text',
  title = 'Belum ada data',
  description,
  actionLabel,
  onAction,
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 px-6 text-center">
      <span className="text-[var(--color-text-mute)]">
        <Icon name={icon} size={40} strokeWidth={1.5} />
      </span>
      <div className="flex flex-col gap-1 max-w-xs">
        <Text variant="h3" className="text-ink">
          {title}
        </Text>
        {description && (
          <Text variant="caption">
            {description}
          </Text>
        )}
      </div>
      {actionLabel && onAction && (
        <Button variant="ghost" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

export default memo(EmptyState);

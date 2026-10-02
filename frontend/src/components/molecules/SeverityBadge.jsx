import { memo } from 'react';
import Badge from '../atoms/Badge';

const LEVEL_MAP = {
  critical: { variant: 'critical', label: 'Critical' },
  high:     { variant: 'high',     label: 'High' },
  medium:   { variant: 'warning',  label: 'Medium' },
  low:      { variant: 'success',  label: 'Low' },
};

function SeverityBadge({ level }) {
  const key = (level ?? '').toLowerCase();
  const { variant, label } = LEVEL_MAP[key] ?? { variant: 'muted', label: level ?? '—' };
  return <Badge variant={variant}>{label}</Badge>;
}

export default memo(SeverityBadge);

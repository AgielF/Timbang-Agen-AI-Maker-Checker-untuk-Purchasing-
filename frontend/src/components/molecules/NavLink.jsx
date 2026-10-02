import { memo } from 'react';
import { Link, useMatch } from 'react-router-dom';

function NavLink({ to, active, children }) {
  // If `active` is not passed explicitly, infer from route match
  const matched = useMatch(to);
  const isActive = active !== undefined ? active : !!matched;

  return (
    <Link
      to={to}
      className={[
        'text-sm font-medium transition-colors px-3 py-2 rounded-md',
        isActive
          ? 'text-electric'
          : 'text-[var(--color-text-mute)] hover:text-ink',
      ].join(' ')}
    >
      {children}
    </Link>
  );
}

export default memo(NavLink);

import { Link } from 'react-router-dom';
import NavLink from '../molecules/NavLink';
import Button from '../atoms/Button';

const NAV_LINKS = [
  { to: '/product', label: 'Product' },
  { to: '/research', label: 'Research' },
  { to: '/docs', label: 'Docs' },
];

function NavBar({ activePath = '' }) {
  return (
    <header
      className="sticky top-0 z-50 h-16 bg-canvas/80 backdrop-blur-md border-b border-[var(--border-light)]"
    >
      <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between gap-8">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2 text-navy no-underline"
          aria-label="Timbang — home"
        >
          <span className="text-xl font-black tracking-tight text-navy leading-none">
            Timbang
          </span>
          <span
            className="w-2 h-2 rounded-full bg-electric flex-shrink-0"
            aria-hidden="true"
          />
        </Link>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              active={activePath === to}
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* CTA */}
        <Button as={Link} to="/dashboard" variant="primary" size="sm">
          Launch App
        </Button>
      </div>
    </header>
  );
}

export default NavBar;

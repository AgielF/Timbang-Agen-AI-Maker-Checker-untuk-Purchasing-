import { Link } from 'react-router-dom';
import AppTemplate from '../components/templates/AppTemplate';
import NavBar from '../components/organisms/NavBar';
import Badge from '../components/atoms/Badge';
import Button from '../components/atoms/Button';
import Icon from '../components/atoms/Icon';

/**
 * ComingSoonPage — reusable Coming Soon page.
 * Props:
 *   title       {string} — page title
 *   description {string} — short description
 *   eta         {string} — optional ETA string
 */
export default function ComingSoonPage({
  title = 'Coming Soon',
  description = 'Fitur ini sedang dalam pengerjaan.',
  eta,
}) {
  return (
    <AppTemplate navbar={<NavBar />}>
      <div className="min-h-[70vh] flex items-center justify-center px-6">
        <div className="flex flex-col items-center text-center gap-6 max-w-lg">
          <Badge variant="warning" size="md">
            Coming Soon
          </Badge>

          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-[var(--color-text-inv)] leading-tight">
            {title}
          </h1>

          <p className="text-base text-[var(--color-text-inv-mute)] leading-relaxed">
            {description}
          </p>

          {eta && (
            <div className="flex items-center gap-1.5 text-sm text-[var(--color-text-inv-mute)]">
              <Icon name="clock" size={14} />
              <span>{eta}</span>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button as={Link} to="/checker" variant="primary" size="md">
              Coba Checker Agent
            </Button>
            <Button as={Link} to="/" variant="ghost" size="md">
              Kembali ke Beranda
            </Button>
          </div>
        </div>
      </div>
    </AppTemplate>
  );
}

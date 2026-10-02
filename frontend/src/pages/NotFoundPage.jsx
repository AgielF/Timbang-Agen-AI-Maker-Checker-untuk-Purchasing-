import { Link } from 'react-router-dom';
import AppTemplate from '../components/templates/AppTemplate';
import NavBar from '../components/organisms/NavBar';
import Footer from '../components/organisms/Footer';
import Button from '../components/atoms/Button';

export default function NotFoundPage() {
  return (
    <AppTemplate
      navbar={<NavBar />}
      footer={<Footer />}
    >
      <div className="flex flex-col items-center justify-center gap-6 py-32 px-6 text-center">
        <p
          className="text-8xl font-black tracking-tighter text-[var(--color-text-inv)] leading-none select-none"
          aria-hidden="true"
        >
          404
        </p>
        <p className="text-lg text-[var(--color-text-inv-mute)]">
          Halaman tidak ditemukan.
        </p>
        <Button as={Link} to="/" variant="primary" size="md">
          Kembali ke beranda
        </Button>
      </div>
    </AppTemplate>
  );
}

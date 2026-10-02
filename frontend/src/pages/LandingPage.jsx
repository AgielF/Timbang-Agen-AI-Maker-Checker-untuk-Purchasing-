import NavBar from '../components/organisms/NavBar';
import Hero from '../components/organisms/Hero';
import StatStrip from '../components/organisms/StatStrip';
import FeatureGrid from '../components/organisms/FeatureGrid';
import HowItWorks from '../components/organisms/HowItWorks';
import ComingSoonGrid from '../components/organisms/ComingSoonGrid';
import CTAStrip from '../components/organisms/CTAStrip';
import Footer from '../components/organisms/Footer';
import LandingTemplate from '../components/templates/LandingTemplate';

const COMING_SOON_ITEMS = [
  {
    icon: 'search',
    title: 'Maker Agent',
    caption: 'Backend ready. UI coming soon.',
  },
  {
    icon: 'external-link',
    title: 'Dashboard',
    caption: 'KPI overview + analytics.',
  },
  {
    icon: 'file-text',
    title: 'Vendor Management',
    caption: 'Master data vendor dan quote.',
  },
  {
    icon: 'clock',
    title: 'Audit History',
    caption: 'Riwayat pemeriksaan dan temuan.',
  },
];

export default function LandingPage() {
  return (
    <div className="bg-canvas font-sans">
      <NavBar />
      <LandingTemplate
        hero={<Hero />}
        stats={<StatStrip />}
        features={<FeatureGrid />}
        howItWorks={<HowItWorks />}
        comingSoon={<ComingSoonGrid items={COMING_SOON_ITEMS} />}
        cta={
          <CTAStrip
            headline="Coba Checker Agent sekarang."
            caption="Three-way matching PO/GR/Invoice + laporan risiko otomatis."
            ctaLabel="Launch Checker"
            ctaTo="/checker"
          />
        }
      />
      <Footer />
    </div>
  );
}

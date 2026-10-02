import NavBar from '../components/organisms/NavBar';
import Hero from '../components/organisms/Hero';
import StatStrip from '../components/organisms/StatStrip';
import FeatureGrid from '../components/organisms/FeatureGrid';
import HowItWorks from '../components/organisms/HowItWorks';
import ComingSoonGrid from '../components/organisms/ComingSoonGrid';
import CTAStrip from '../components/organisms/CTAStrip';
import Footer from '../components/organisms/Footer';
import LandingTemplate from '../components/templates/LandingTemplate';

export default function LandingPage() {
  return (
    <div className="bg-canvas font-sans">
      <NavBar />
      <LandingTemplate
        hero={<Hero />}
        stats={<StatStrip />}
        features={<FeatureGrid />}
        howItWorks={<HowItWorks />}
        comingSoon={<ComingSoonGrid />}
        cta={
          <CTAStrip
            headline="Siap mulai?"
            caption="Coba Maker Agent sekarang."
            ctaLabel="Launch App"
            ctaTo="/dashboard"
          />
        }
      />
      <Footer />
    </div>
  );
}

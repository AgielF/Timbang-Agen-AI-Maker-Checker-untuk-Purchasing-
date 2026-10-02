import { memo } from 'react';

/**
 * LandingTemplate — layout skeleton for the landing page.
 * All slots are optional; omitted slots render nothing.
 *
 * Props:
 *   hero       {ReactNode} — Hero organism
 *   stats      {ReactNode} — StatStrip
 *   features   {ReactNode} — FeatureGrid
 *   howItWorks {ReactNode} — HowItWorks
 *   comingSoon {ReactNode} — ComingSoonGrid
 *   cta        {ReactNode} — CTAStrip
 */
function LandingTemplate({ hero, stats, features, howItWorks, comingSoon, cta }) {
  return (
    <main>
      {hero}
      {stats}
      {features}
      {howItWorks}
      {comingSoon}
      {cta}
    </main>
  );
}

export default memo(LandingTemplate);

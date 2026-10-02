import { useEffect, useRef } from 'react';
import Button from '../atoms/Button';

const HEADLINE_EN = 'Detect procurement fraud before it costs you.';
const HEADLINE_ID = 'Deteksi fraud pengadaan sebelum jadi kerugian.';

const MASK_ACTIVE = (mx, my) =>
  `radial-gradient(circle 280px at ${mx} ${my}, black 0%, transparent 100%)`;
const MASK_CENTER = MASK_ACTIVE('50%', '50%');

function HeroPattern() {
  return (
    <div
      aria-hidden="true"
      className={[
        'pointer-events-none absolute inset-0 select-none overflow-hidden',
        'text-navy/[0.04] font-black tracking-[0.4em]',
        'text-[clamp(1.5rem,4vw,3rem)] leading-[2]',
        'flex flex-col justify-start',
      ].join(' ')}
    >
      {Array.from({ length: 20 }).map((_, i) => (
        <div key={i} className="whitespace-nowrap">
          {Array.from({ length: 10 }).map((_, j) => (
            <span key={j}>T I M B A N G&nbsp;&nbsp;&nbsp;</span>
          ))}
        </div>
      ))}
    </div>
  );
}

function Hero() {
  const heroRef    = useRef(null);
  const overlayRef = useRef(null);
  const rafId      = useRef(null);

  useEffect(() => {
    const hero    = heroRef.current;
    const overlay = overlayRef.current;
    if (!hero || !overlay) return;

    // Skip interaction on touch devices and when user prefers reduced motion
    const noHover       = window.matchMedia('(hover: none)').matches;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (noHover || reducedMotion) {
      overlay.style.display = 'none';
      return;
    }

    // Apply initial mask at center
    overlay.style.webkitMaskImage = MASK_CENTER;
    overlay.style.maskImage = MASK_CENTER;
    overlay.style.transition = '--mx 0.05s ease-out, --my 0.05s ease-out';

    function handleMove(e) {
      if (rafId.current) cancelAnimationFrame(rafId.current);
      rafId.current = requestAnimationFrame(() => {
        const rect = hero.getBoundingClientRect();
        const mx   = ((e.clientX - rect.left)  / rect.width  * 100).toFixed(2) + '%';
        const my   = ((e.clientY - rect.top)   / rect.height * 100).toFixed(2) + '%';
        overlay.style.webkitMaskImage = MASK_ACTIVE(mx, my);
        overlay.style.maskImage = MASK_ACTIVE(mx, my);
      });
    }

    function handleLeave() {
      if (rafId.current) cancelAnimationFrame(rafId.current);
      rafId.current = requestAnimationFrame(() => {
        overlay.style.webkitMaskImage = MASK_CENTER;
        overlay.style.maskImage = MASK_CENTER;
      });
    }

    hero.addEventListener('mousemove', handleMove);
    hero.addEventListener('mouseleave', handleLeave);

    return () => {
      hero.removeEventListener('mousemove', handleMove);
      hero.removeEventListener('mouseleave', handleLeave);
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, []);

  return (
    <section
      ref={heroRef}
      aria-label="Hero section — Timbang"
      className="relative overflow-hidden bg-canvas"
    >
      {/* Background pattern */}
      <HeroPattern />

      {/* Content wrapper */}
      <div className="relative max-w-7xl mx-auto px-6 py-32 md:py-48">
        {/* Headline layer */}
        <div className="relative">
          {/* Base layer — Indonesian (always visible) */}
          <h1
            className={[
              'text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-[0.95]',
              'text-navy',
            ].join(' ')}
          >
            {HEADLINE_ID}
          </h1>

          {/* Overlay layer — English (visible through spotlight mask) */}
          <h1
            ref={overlayRef}
            aria-hidden="true"
            className={[
              'absolute inset-0',
              'text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-[0.95]',
              'text-electric',
            ].join(' ')}
          >
            {HEADLINE_EN}
          </h1>
        </div>

        {/* Sub-headline */}
        <p className="mt-8 text-lg md:text-xl text-[var(--color-text-mute)] max-w-xl leading-relaxed">
          AI Maker–Checker untuk deteksi fraud pengadaan di perusahaan menengah Indonesia.
          Tanpa ERP, tanpa setup rumit.
        </p>

        {/* CTA buttons */}
        <div className="mt-10 flex flex-wrap gap-4">
          <Button
            variant="primary"
            size="lg"
            onClick={() => { window.location.href = '/dashboard'; }}
          >
            Lihat Demo
          </Button>
          <Button
            variant="ghost"
            size="lg"
            onClick={() => { window.location.href = '/docs'; }}
          >
            Baca Docs
          </Button>
        </div>
      </div>
    </section>
  );
}

export default Hero;

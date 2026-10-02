import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Button from '../atoms/Button';

const HEADLINE_EN = 'Detect procurement fraud before it costs you.';
const HEADLINE_ID = 'Deteksi fraud pengadaan sebelum jadi kerugian.';

const HEADLINE_CLASS =
  'text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-[0.95]';

const REVEAL_RADIUS = 220;

const hiddenGradient = 'radial-gradient(circle 0px at 50% 50%, transparent 0%, transparent 100%)';
const makeRevealGradient = (x, y) =>
  `radial-gradient(circle ${REVEAL_RADIUS}px at ${x}px ${y}px, #508DFF 0%, #508DFF 40%, rgba(80,141,255,0) 70%)`;

export default function Hero() {
  const heroRef = useRef(null);
  const overlayRef = useRef(null);

  useEffect(() => {
    const hero = heroRef.current;
    const overlay = overlayRef.current;
    if (!hero || !overlay) return;

    const isTouch = window.matchMedia('(hover: none) and (pointer: coarse)').matches;
    if (isTouch) {
      overlay.style.display = 'none';
      return;
    }

    overlay.style.backgroundImage = hiddenGradient;

    const onMove = (e) => {
      const rect = overlay.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      overlay.style.backgroundImage = makeRevealGradient(x, y);
    };

    const onLeave = () => {
      overlay.style.backgroundImage = hiddenGradient;
    };

    hero.addEventListener('mousemove', onMove);
    hero.addEventListener('mouseleave', onLeave);
    return () => {
      hero.removeEventListener('mousemove', onMove);
      hero.removeEventListener('mouseleave', onLeave);
    };
  }, []);

  return (
    <section
      ref={heroRef}
      className="relative isolate overflow-hidden border-b border-[var(--border-light)] bg-canvas"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 select-none overflow-hidden text-[110px] font-black leading-[1.35] tracking-[0.4em] text-navy opacity-[0.04]"
      >
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="whitespace-nowrap">
            T I M B A N G &nbsp;&nbsp; T I M B A N G &nbsp;&nbsp; T I M B A N G
          </div>
        ))}
      </div>
      <div className="relative z-10 mx-auto max-w-7xl px-6 py-32 md:py-40">
        <div className="relative">
          <h1 className={`${HEADLINE_CLASS} text-navy`}>
            {HEADLINE_EN}
          </h1>
          <h1
            ref={overlayRef}
            aria-hidden="true"
            style={{
              color: 'transparent',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              backgroundImage: hiddenGradient,
            }}
            className={`${HEADLINE_CLASS} absolute inset-0 pointer-events-none`}
          >
            {HEADLINE_ID}
          </h1>
        </div>
        <p className="mt-8 max-w-2xl text-base md:text-lg text-[var(--color-text-mute)]">
          AI Maker-Checker untuk deteksi fraud pengadaan di perusahaan
          menengah Indonesia. Tanpa ERP, tanpa setup rumit.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Button as={Link} to="/maker" variant="primary" size="lg">
            Lihat Demo
          </Button>
          <Button as={Link} to="/about" variant="ghost" size="lg">
            Baca Docs
          </Button>
        </div>
      </div>
    </section>
  );
}

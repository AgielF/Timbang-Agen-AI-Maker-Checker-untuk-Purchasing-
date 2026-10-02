import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Button from '../atoms/Button';

const HEADLINE_EN = 'Detect procurement fraud before it costs you.';
const HEADLINE_ID = 'Deteksi fraud pengadaan sebelum jadi kerugian.';

const HEADLINE_CLASS =
  'text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter leading-[0.95]';

const REVEAL_RADIUS = 480;

// EN: navy di luar circle, transparent di dalam circle (EN hilang di area reveal)
const EN_OUTSIDE = (x, y) =>
  `radial-gradient(circle ${REVEAL_RADIUS}px at ${x}px ${y}px, transparent 0%, transparent 97%, #0F2A47 99%)`;

// ID: transparent di luar circle, electric blue di dalam circle (ID muncul di area reveal)
const ID_INSIDE = (x, y) =>
  `radial-gradient(circle ${REVEAL_RADIUS}px at ${x}px ${y}px, #508DFF 0%, #508DFF 97%, transparent 99%)`;

const HIDDEN_POS = -9999;
const EN_INIT = EN_OUTSIDE(HIDDEN_POS, HIDDEN_POS);
const ID_INIT = ID_INSIDE(HIDDEN_POS, HIDDEN_POS);

export default function Hero() {
  const heroRef = useRef(null);
  const baseRef = useRef(null);
  const overlayRef = useRef(null);

  useEffect(() => {
    const hero = heroRef.current;
    const base = baseRef.current;
    const overlay = overlayRef.current;
    if (!hero || !base || !overlay) return;

    const isTouch = window.matchMedia('(hover: none) and (pointer: coarse)').matches;
    if (isTouch) {
      overlay.style.display = 'none';
      return;
    }

    const onMove = (e) => {
      const rect = hero.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      base.style.backgroundImage = EN_OUTSIDE(x, y);
      overlay.style.backgroundImage = ID_INSIDE(x, y);
    };

    const onLeave = () => {
      base.style.backgroundImage = EN_INIT;
      overlay.style.backgroundImage = ID_INIT;
    };

    hero.addEventListener('mousemove', onMove);
    hero.addEventListener('mouseleave', onLeave);
    document.addEventListener('mouseleave', onLeave);

    return () => {
      hero.removeEventListener('mousemove', onMove);
      hero.removeEventListener('mouseleave', onLeave);
      document.removeEventListener('mouseleave', onLeave);
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
          {/* Base EN — navy muncul di luar circle, hilang di dalam circle */}
          <h1
            ref={baseRef}
            style={{
              color: 'transparent',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              backgroundImage: EN_INIT,
            }}
            className={HEADLINE_CLASS}
          >
            {HEADLINE_EN}
          </h1>

          {/* Overlay ID — electric blue muncul di dalam circle saja */}
          <h1
            ref={overlayRef}
            aria-hidden="true"
            style={{
              color: 'transparent',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              backgroundImage: ID_INIT,
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
          <Button as={Link} to="/checker" variant="primary" size="lg">
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

import { memo } from 'react';
import { Link } from 'react-router-dom';
import Button from '../atoms/Button';

function CTAStrip({
  headline = 'Mulai deteksi fraud hari ini.',
  caption = 'Gratis selama hackathon. Tanpa kartu kredit.',
  ctaLabel = 'Coba Sekarang',
  ctaTo = '/',
}) {
  return (
    <section
      aria-label="Call to action"
      className="border-y border-[var(--border-light)] py-24 md:py-32"
    >
      <div className="max-w-7xl mx-auto px-6 flex flex-col items-center text-center gap-6">
        <h2 className="text-4xl md:text-6xl font-black tracking-tight text-ink max-w-2xl leading-[0.95]">
          {headline}
        </h2>
        <p className="text-base text-[var(--color-text-mute)] max-w-md">
          {caption}
        </p>
        <Button as={Link} to={ctaTo} variant="primary" size="lg">
          {ctaLabel}
        </Button>
      </div>
    </section>
  );
}

export default memo(CTAStrip);

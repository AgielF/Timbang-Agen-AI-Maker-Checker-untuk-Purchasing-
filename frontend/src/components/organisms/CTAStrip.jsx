import { memo } from 'react';
import CTABlock from '../molecules/CTABlock';

function CTAStrip() {
  return (
    <section
      aria-label="Call to action"
      className="border-y border-[var(--border-light)] py-24 md:py-32"
    >
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-8">
          <CTABlock
            title="Coba Checker Agent sekarang"
            description="Three-way matching PO/GR/Invoice + laporan risiko otomatis"
            buttonLabel="Launch Checker"
            buttonHref="/checker"
            variant="primary"
          />
          <CTABlock
            title="Coba Maker Agent sekarang"
            description="Ekstrak penawaran vendor + cross-validate harga pasar live"
            buttonLabel="Launch Maker"
            buttonHref="/maker"
            variant="secondary"
          />
        </div>
      </div>
    </section>
  );
}

export default memo(CTAStrip);

import { memo } from 'react';

const DEFAULT_STEPS = [
  {
    number: '01',
    title: 'Submit',
    caption: 'Upload data vendor dan quote.',
  },
  {
    number: '02',
    title: 'Validate',
    caption: 'AI cross-validates harga pasar.',
  },
  {
    number: '03',
    title: 'Decide',
    caption: 'Rekomendasi + laporan risiko.',
  },
];

function HowItWorks({ steps = DEFAULT_STEPS }) {
  return (
    <section aria-label="How it works" className="border-y border-[var(--border-light)]">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-ink mb-10">
          How it works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[var(--border-light)]">
          {steps.map(({ number, title, caption }) => (
            <div
              key={number}
              className="relative p-6 md:p-8 border border-[var(--border-light)] md:border-0"
            >
              {/* Step number as large background text */}
              <span
                className="absolute top-4 right-6 text-6xl font-black text-navy/10 select-none leading-none"
                aria-hidden="true"
              >
                {number}
              </span>
              <div className="relative flex flex-col gap-2">
                <span className="text-xs font-medium text-electric uppercase tracking-widest">
                  {number}
                </span>
                <h3 className="text-xl font-semibold text-ink">{title}</h3>
                <p className="text-sm text-[var(--color-text-mute)] leading-relaxed">
                  {caption}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default memo(HowItWorks);

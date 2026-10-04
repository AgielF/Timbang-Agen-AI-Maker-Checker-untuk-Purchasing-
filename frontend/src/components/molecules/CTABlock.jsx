import { memo } from 'react';
import { Link } from 'react-router-dom';
import Button from '../atoms/Button';

function CTABlock({ title, description, buttonLabel, buttonHref, variant = 'primary' }) {
  return (
    <div className="flex flex-col items-start gap-4 p-6 border border-[var(--border-light)] hover:border-electric/40 transition-colors bg-canvas text-left h-full">
      <h3 className="text-2xl font-black tracking-tight text-ink">
        {title}
      </h3>
      <p className="text-base text-[var(--color-text-mute)] flex-grow">
        {description}
      </p>
      <div className="pt-4 mt-auto">
        <Button as={Link} to={buttonHref} variant={variant} size="lg">
          {buttonLabel}
        </Button>
      </div>
    </div>
  );
}

export default memo(CTABlock);

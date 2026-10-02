import { memo } from 'react';
import Icon from '../atoms/Icon';
import Spinner from '../atoms/Spinner';
import Button from '../atoms/Button';

const STEPS = [
  'Fetching quotes',
  'Cross-validating prices',
  'Querying LLM',
  'Composing recommendation',
];

/**
 * LoadingSteps — animated 4-step progress indicator.
 * Props:
 *   currentStep {number} 0-based index of active step (default 0)
 *   onCancel    {Function}
 */
function LoadingSteps({ currentStep = 0, onCancel }) {
  return (
    <div className="flex flex-col gap-6 py-8 px-6">
      {/* Indeterminate bar */}
      <div className="h-1 w-full bg-ink/10 overflow-hidden rounded-full">
        <div className="h-full w-1/2 bg-electric animate-pulse rounded-full" />
      </div>

      <ol className="flex flex-col gap-3">
        {STEPS.map((step, i) => {
          const done    = i < currentStep;
          const active  = i === currentStep;
          const pending = i > currentStep;

          return (
            <li key={step} className="flex items-center gap-3">
              <span
                className={[
                  'flex items-center justify-center w-6 h-6 rounded-full border shrink-0 transition-colors',
                  done
                    ? 'border-emerald text-emerald bg-emerald/10'
                    : active
                    ? 'border-electric text-electric bg-electric/10'
                    : 'border-[var(--border-light)] text-[var(--color-text-mute)]',
                ].join(' ')}
              >
                {done ? (
                  <Icon name="check" size={14} />
                ) : active ? (
                  <Spinner size="sm" />
                ) : (
                  <span className="text-[10px] font-mono">{i + 1}</span>
                )}
              </span>

              <span
                className={[
                  'text-sm font-medium transition-colors',
                  done    ? 'text-emerald'                    : '',
                  active  ? 'text-electric'                   : '',
                  pending ? 'text-[var(--color-text-mute)]'  : '',
                ].join(' ')}
              >
                {step}
              </span>
            </li>
          );
        })}
      </ol>

      <p className="text-xs text-[var(--color-text-mute)] font-mono tabular-nums">~60 detik</p>

      {onCancel && (
        <Button variant="ghost" size="sm" className="self-start" onClick={onCancel}>
          Cancel
        </Button>
      )}
    </div>
  );
}

export default memo(LoadingSteps);

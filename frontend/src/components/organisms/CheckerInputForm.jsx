import { memo } from 'react';
import Button from '../atoms/Button';
import Icon from '../atoms/Icon';
import DocumentInputGroup from '../molecules/DocumentInputGroup';

function CheckerInputForm({
  value,
  onChange,
  onSubmit,
  loading = false,
  hasL2 = false,
  hasDocs = true,
  onHasL2Change,
  onHasDocsChange,
  onReset,
}) {
  const updateDocument = (key, document) => {
    onChange({ ...value, [key]: document });
  };

  return (
    <details open className="group border border-[var(--border-dark)] bg-surface text-ink">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 [&::-webkit-details-marker]:hidden">
        <span className="flex items-center gap-2">
          <Icon name="file-text" size={18} className="text-electric" />
          <span className="text-sm font-semibold uppercase tracking-wider">Input dokumen checker</span>
        </span>
        <Icon name="chevron-down" size={18} className="text-[var(--color-text-mute)] transition-transform group-open:rotate-180" />
      </summary>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
        className="flex flex-col gap-5 border-t border-[var(--border-light)] px-5 py-5"
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <DocumentInputGroup
            title="Purchase Order"
            value={value.po}
            onChange={(document) => updateDocument('po', document)}
          />
          <DocumentInputGroup
            title="Goods Receipt"
            value={value.gr}
            onChange={(document) => updateDocument('gr', document)}
          />
          <div className="lg:col-span-2">
            <DocumentInputGroup
              title="Invoice"
              value={value.invoice}
              onChange={(document) => updateDocument('invoice', document)}
              withTaxFields
            />
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <label className="flex cursor-pointer items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={hasL2}
              onChange={(event) => onHasL2Change(event.target.checked)}
              className="h-4 w-4 accent-electric"
            />
            Has Level 2 Approval
          </label>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={hasDocs}
              onChange={(event) => onHasDocsChange(event.target.checked)}
              className="h-4 w-4 accent-electric"
            />
            Has Complete Docs
          </label>
          <div className="flex gap-2 sm:ml-auto">
            {onReset && (
              <Button type="button" variant="ghost" size="md" onClick={onReset}>
                Reset ke Sampel
              </Button>
            )}
            <Button type="submit" variant="primary" size="md" loading={loading}>
              Run Checker
            </Button>
          </div>
        </div>
      </form>
    </details>
  );
}

export default memo(CheckerInputForm);

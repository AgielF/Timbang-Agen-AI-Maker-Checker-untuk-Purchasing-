import { memo, useId } from 'react';
import Badge from '../atoms/Badge';
import FormField from './FormField';
import Icon from '../atoms/Icon';

const ICON_BY_TITLE = {
  'purchase order': 'file-text',
  'goods receipt': 'check',
  invoice: 'dollar-sign',
};

const BASE_FIELDS = [
  { name: 'reference', label: 'Reference', type: 'text', placeholder: 'PO-2026-001' },
  { name: 'quantity', label: 'Quantity', type: 'number', min: '0', step: 'any' },
  { name: 'amount', label: 'Amount', type: 'number', min: '0', step: 'any' },
];

const TAX_FIELDS = [
  { name: 'tax_invoice_ref', label: 'Nomor Faktur Pajak', type: 'text', placeholder: '010.000-26.00000001' },
  { name: 'dpp_amount', label: 'DPP', type: 'number', min: '0', step: 'any' },
  { name: 'ppn_amount', label: 'PPN', type: 'number', min: '0', step: 'any' },
  { name: 'npwp_vendor', label: 'NPWP Vendor', type: 'text', placeholder: '15 digit NPWP' },
];

function DocumentInputGroup({ title, value = {}, onChange, withTaxFields = false }) {
  const currencyId = useId();
  const icon = ICON_BY_TITLE[title.toLowerCase()] ?? 'file-text';
  const fields = withTaxFields ? [...BASE_FIELDS, ...TAX_FIELDS] : BASE_FIELDS;

  const updateField = (name, nextValue) => {
    onChange({ ...value, [name]: nextValue });
  };

  return (
    <section className="border border-[var(--border-dark)] bg-surface p-4 text-ink">
      <header className="mb-4 flex items-center gap-2 border-b border-[var(--border-light)] pb-3">
        <span className="text-electric"><Icon name={icon} size={18} /></span>
        <h3 className="text-sm font-semibold uppercase tracking-wider">{title}</h3>
        {withTaxFields && <Badge variant="warning" size="sm">Faktur Pajak</Badge>}
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {fields.map((field) => (
          <FormField
            key={field.name}
            label={field.label}
            type={field.type}
            value={value[field.name] ?? ''}
            placeholder={field.placeholder}
            min={field.min}
            step={field.step}
            inputMode={field.type === 'number' ? 'decimal' : undefined}
            onChange={(event) => updateField(field.name, event.target.value)}
          />
        ))}
        <div className="flex flex-col gap-1">
          <label htmlFor={currencyId} className="text-sm font-medium text-ink">
            Currency
          </label>
          <select
            id={currencyId}
            value={value.currency ?? 'IDR'}
            onChange={(event) => updateField('currency', event.target.value)}
            className="w-full rounded-md border border-[var(--border-light)] bg-white px-3 py-2 text-base text-ink outline-none transition-colors focus:border-electric focus:ring-2 focus:ring-electric/50"
          >
            <option value="IDR">IDR — Rupiah</option>
            <option value="USD">USD — US Dollar</option>
          </select>
        </div>
      </div>
    </section>
  );
}

export default memo(DocumentInputGroup);

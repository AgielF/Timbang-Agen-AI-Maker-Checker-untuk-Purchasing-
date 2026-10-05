import { memo } from 'react';
import Badge from '../atoms/Badge';

const INDICATIONS = {
  PRICE_MANIPULATION: { variant: 'critical', label: 'Manipulasi Harga' },
  QTY_DISCREPANCY: { variant: 'warning', label: 'Selisih Kuantitas' },
  SPLIT_PO: { variant: 'high', label: 'Split PO' },
  DUPLICATE_INVOICE: { variant: 'critical', label: 'Invoice Ganda' },
  UNAUTHORIZED_APPROVAL: { variant: 'high', label: 'Approval Tidak Sah' },
  INCOMPLETE_DOCS: { variant: 'medium', label: 'Dokumen Tidak Lengkap' },
  UNKNOWN: { variant: 'muted', label: 'Tidak Terklasifikasi' },
};

function IndicationBadge({ value }) {
  const key = (value ?? 'UNKNOWN').toUpperCase();
  const { variant, label } = INDICATIONS[key] ?? INDICATIONS.UNKNOWN;
  return <Badge variant={variant}>{label}</Badge>;
}

export default memo(IndicationBadge);

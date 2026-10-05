export const ROUTES = {
  LANDING: '/',
  DASHBOARD: '/dashboard',
  MAKER: '/maker',
  VALIDATE: '/maker/validate',
  CHECKER: '/checker',
  RISK_REPORT: '/checker/risk-report',
  VENDORS: '/vendors',
  FINDINGS: '/findings',
  ABOUT: '/about',
};

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const SAMPLE_TRANSACTION_ID = 'TRX-2026-001'

export const SAMPLE_DOCS = {
  po:      { quantity: 100, amount: 10000000, currency: 'IDR', reference: 'PO-2026-001', npwp_vendor: '012345678901234' },
  gr:      { quantity: 95,  amount: 9500000,  currency: 'IDR', reference: 'GR-2026-001' },
  invoice: {
    quantity: 100,
    amount: 11100000,
    currency: 'IDR',
    reference: 'INV-2026-001',
    tax_invoice_ref: '010.000-26.00000001',
    ppn_amount: 1100000,
    npwp_vendor: '012345678901234',
    dpp_amount: 10000000,
  },
}

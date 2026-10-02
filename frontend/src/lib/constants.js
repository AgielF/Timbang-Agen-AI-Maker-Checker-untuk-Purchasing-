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

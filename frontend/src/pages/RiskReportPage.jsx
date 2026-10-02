import { useSearchParams } from 'react-router-dom';
import WorkbenchTemplate from '../components/templates/WorkbenchTemplate';
import NavBar from '../components/organisms/NavBar';
import FindingList from '../components/organisms/FindingList';
import Button from '../components/atoms/Button';
import Badge from '../components/atoms/Badge';

const REPORT_TS = '2026-09-30T10:00:00Z';

const SAMPLE_FINDINGS = [
  { id: 1, transaction_id: 'TRX-001', severity: 'high',   message: 'Invoice melebihi PO sebesar 5%.',              created_at: '2026-09-30T10:00:00Z' },
  { id: 2, transaction_id: 'TRX-001', severity: 'high',   message: 'Tidak ada approval untuk selisih harga.',       created_at: '2026-09-30T10:01:00Z' },
  { id: 3, transaction_id: 'TRX-001', severity: 'medium', message: 'Tanggal GR lebih awal dari tanggal PO.',        created_at: '2026-09-30T10:02:00Z' },
  { id: 4, transaction_id: 'TRX-001', severity: 'low',    message: 'Referensi vendor tidak cocok dengan database.', created_at: '2026-09-30T10:03:00Z' },
  { id: 5, transaction_id: 'TRX-001', severity: 'low',    message: 'Nomor PO tidak ditemukan di sistem internal.',  created_at: '2026-09-30T10:04:00Z' },
];

const SAMPLE_BREAKDOWN = { critical: 0, high: 2, medium: 1, low: 3 };
const RISK_SCORE       = 72;
const SOP_RESULT       = {
  passed:     false,
  violations: [
    'Invoice melebihi PO sebesar 5%',
    'Tidak ada approval untuk selisih harga',
  ],
};
const RECOMMENDED_ACTIONS = [
  'Investigasi approval untuk selisih harga',
  'Konfirmasi ke vendor mengenai kuantitas',
  'Flag vendor untuk review berkala',
];

const SEV_COLORS = { critical: 'bg-sev-critical', high: 'bg-sev-high', medium: 'bg-sev-medium', low: 'bg-sev-low' };
const SEV_TEXT   = { critical: 'text-sev-critical', high: 'text-sev-high', medium: 'text-sev-medium', low: 'text-sev-low' };

const fmtTs = (iso) => {
  try { return new Date(iso).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }); }
  catch { return iso; }
};

function RiskGauge({ score }) {
  const pct   = Math.min(100, Math.max(0, score));
  const color = pct >= 70 ? 'bg-sev-high' : pct >= 40 ? 'bg-sev-medium' : 'bg-sev-low';
  return (
    <div className="border border-[var(--border-dark)] bg-surface p-6 flex flex-col gap-3">
      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-inv-mute)]">Risk Score</span>
      <div className="flex items-end gap-3">
        <span className="font-mono tabular-nums text-5xl font-black text-[var(--color-text-inv)]">{score}</span>
        <span className="text-[var(--color-text-inv-mute)] text-sm pb-1">/ 100</span>
      </div>
      <div className="h-2 w-full bg-surface-2 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function SeverityBreakdown({ counts }) {
  const total = Object.values(counts).reduce((s, v) => s + v, 0) || 1;
  return (
    <div className="border border-[var(--border-dark)] bg-surface p-6 flex flex-col gap-4">
      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-inv-mute)]">Severity Breakdown</span>
      {Object.entries(counts).map(([sev, count]) => (
        <div key={sev} className="flex items-center gap-3">
          <span className={`w-16 text-xs font-semibold uppercase ${SEV_TEXT[sev] ?? 'text-[var(--color-text-inv-mute)]'}`}>{sev}</span>
          <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${SEV_COLORS[sev] ?? 'bg-electric'}`} style={{ width: `${(count / total) * 100}%` }} />
          </div>
          <span className="w-4 text-right text-xs font-mono tabular-nums text-[var(--color-text-inv-mute)]">{count}</span>
        </div>
      ))}
    </div>
  );
}

function SopPanel({ result }) {
  const cls = result.passed ? 'border-emerald/30 bg-emerald/5 text-emerald' : 'border-sev-high/30 bg-sev-high/5 text-sev-high';
  return (
    <div className={`border p-6 flex flex-col gap-3 ${cls.split(' ').slice(0, 2).join(' ')}`}>
      <span className={`text-xs font-semibold uppercase tracking-wider ${result.passed ? 'text-emerald' : 'text-sev-high'}`}>
        SOP Validation — {result.passed ? 'PASSED' : 'FAILED'}
      </span>
      {!result.passed && result.violations.map((v) => (
        <div key={v} className="flex items-start gap-2 text-sm text-[var(--color-text-inv)]">
          <span className="text-sev-high mt-0.5 shrink-0">✕</span>
          {v}
        </div>
      ))}
    </div>
  );
}

export default function RiskReportPage() {
  const [searchParams] = useSearchParams();
  const txId = searchParams.get('tx') ?? 'TRX-001';

  return (
    <WorkbenchTemplate
      navbar={<NavBar activePath="/checker/risk-report" />}
      header={
        <div className="flex items-start justify-between gap-4 border-b border-[var(--border-light)] pb-6 mb-8">
          <div className="flex flex-col gap-1">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-[var(--color-text-inv)]">
              Risk Report
            </h2>
            <p className="text-sm text-[var(--color-text-inv-mute)]">
              Transaction: <span className="font-mono">{txId}</span>
              <span className="mx-2">·</span>
              {fmtTs(REPORT_TS)}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0 mt-1">
            <Button variant="ghost" size="sm" disabled>Export PDF</Button>
            <Badge variant="warning">Coming Soon</Badge>
          </div>
        </div>
      }
      inputZone={null}
      resultZone={
        <div className="flex flex-col gap-6">
          {/* Row 1: Gauge + Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <RiskGauge score={RISK_SCORE} />
            <SeverityBreakdown counts={SAMPLE_BREAKDOWN} />
          </div>

          {/* Row 2: Summary */}
          <div className="border border-amber/30 bg-amber/10 px-5 py-4">
            <p className="text-sm font-semibold text-amber">
              Risiko tinggi: invoice melebihi PO sebesar 5%.
            </p>
          </div>

          {/* Row 3: SOP */}
          <SopPanel result={SOP_RESULT} />

          {/* Row 4: Findings */}
          <section className="flex flex-col gap-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-inv-mute)]">
              Temuan
            </h3>
            <FindingList items={SAMPLE_FINDINGS} />
          </section>

          {/* Row 5: Recommended Actions */}
          <section className="flex flex-col gap-3 border border-[var(--border-dark)] bg-surface p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-inv-mute)]">
              Recommended Actions
            </h3>
            <ul className="flex flex-col gap-2">
              {RECOMMENDED_ACTIONS.map((action) => (
                <li key={action} className="flex items-start gap-2 text-sm text-[var(--color-text-inv)]">
                  <span className="text-electric mt-0.5 shrink-0">→</span>
                  {action}
                </li>
              ))}
            </ul>
          </section>
        </div>
      }
    />
  );
}

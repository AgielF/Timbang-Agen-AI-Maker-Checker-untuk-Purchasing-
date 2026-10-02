import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WorkbenchTemplate from '../components/templates/WorkbenchTemplate';
import NavBar from '../components/organisms/NavBar';
import PageHeader from '../components/organisms/PageHeader';
import MatchGrid from '../components/organisms/MatchGrid';
import Button from '../components/atoms/Button';
import Icon from '../components/atoms/Icon';

const SAMPLE_PO      = { id: 'PO-2026-0912', vendor: 'PT Maju Jaya', amount: 100_000_000, qty: 100, date: '2026-09-20' };
const SAMPLE_GR      = { id: 'GR-2026-0915', received: 100, received_date: '2026-09-28' };
const SAMPLE_INVOICE = { id: 'INV-2026-0918', amount: 105_000_000, qty: 100, date: '2026-09-30' };
const SAMPLE_DIFFS   = ['amount'];
const SAMPLE_STATUS  = 'discrepancy';

const fmtIDR = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 });

const DIFF_ROWS = [
  { field: 'amount', po: SAMPLE_PO.amount, gr: null, inv: SAMPLE_INVOICE.amount },
];

function VerdictBanner() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 border border-amber/30 bg-amber/10">
      <span className="text-amber shrink-0"><Icon name="alert-triangle" size={16} /></span>
      <div>
        <span className="text-sm font-semibold uppercase tracking-wider text-amber">Discrepancy</span>
        <span className="text-sm text-[var(--color-text-inv-mute)] ml-2">— Invoice 5% di atas PO</span>
      </div>
    </div>
  );
}

function DiffTable() {
  return (
    <div className="border border-[var(--border-dark)] overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border-dark)] bg-surface">
            <th className="text-left px-4 py-2 text-xs font-medium uppercase tracking-wider text-[var(--color-text-inv-mute)]">Field</th>
            <th className="text-right px-4 py-2 text-xs font-medium uppercase tracking-wider text-[var(--color-text-inv-mute)]">PO</th>
            <th className="text-right px-4 py-2 text-xs font-medium uppercase tracking-wider text-[var(--color-text-inv-mute)]">GR</th>
            <th className="text-right px-4 py-2 text-xs font-medium uppercase tracking-wider text-[var(--color-text-inv-mute)]">Invoice</th>
            <th className="text-right px-4 py-2 text-xs font-medium uppercase tracking-wider text-[var(--color-text-inv-mute)]">Delta</th>
          </tr>
        </thead>
        <tbody>
          {DIFF_ROWS.map(({ field, po, gr, inv }) => {
            const delta = po && inv ? inv - po : null;
            return (
              <tr key={field} className="border-b border-[var(--border-dark)] last:border-0 bg-amber/5">
                <td className="px-4 py-2 font-medium text-amber uppercase text-xs tracking-wider">{field}</td>
                <td className="px-4 py-2 text-right font-mono tabular-nums text-[var(--color-text-inv)]">{po != null ? fmtIDR.format(po) : '—'}</td>
                <td className="px-4 py-2 text-right font-mono tabular-nums text-[var(--color-text-inv-mute)]">{gr != null ? fmtIDR.format(gr) : '—'}</td>
                <td className="px-4 py-2 text-right font-mono tabular-nums text-amber">{inv != null ? fmtIDR.format(inv) : '—'}</td>
                <td className="px-4 py-2 text-right font-mono tabular-nums text-sev-high">{delta != null ? '+' + fmtIDR.format(delta) : '—'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function CheckerPage() {
  const [txId, setTxId]         = useState('TRX-001');
  const [showMatch, setShowMatch] = useState(false);
  const [activeTx, setActiveTx]  = useState('TRX-001');
  const navigate = useNavigate();

  function handleRun() {
    setActiveTx(txId.trim() || 'TRX-001');
    setShowMatch(true);
  }

  return (
    <WorkbenchTemplate
      navbar={<NavBar activePath="/checker" />}
      header={<PageHeader title="Checker Agent" />}
      inputZone={
        <div className="flex gap-2">
          <input
            type="text"
            value={txId}
            onChange={(e) => setTxId(e.target.value)}
            placeholder="Masukkan transaction ID…"
            className="flex-1 bg-surface border border-[var(--border-dark)] text-[var(--color-text-inv)] placeholder:text-[var(--color-text-inv-mute)] px-4 py-2 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-electric/50"
          />
          <Button variant="primary" size="md" onClick={handleRun}>
            Run Three-Way Match
          </Button>
        </div>
      }
      resultZone={
        showMatch ? (
          <div className="flex flex-col gap-4">
            <VerdictBanner />
            <MatchGrid
              po={SAMPLE_PO}
              gr={SAMPLE_GR}
              invoice={SAMPLE_INVOICE}
              differences={SAMPLE_DIFFS}
              status={SAMPLE_STATUS}
            />
            <DiffTable />
            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                size="lg"
                onClick={() => navigate(`/checker/risk-report?tx=${encodeURIComponent(activeTx)}`)}
              >
                Generate Risk Report
              </Button>
            </div>
          </div>
        ) : null
      }
    />
  );
}

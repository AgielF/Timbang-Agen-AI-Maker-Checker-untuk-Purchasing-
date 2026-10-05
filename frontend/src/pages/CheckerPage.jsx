import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import WorkbenchTemplate from '../components/templates/WorkbenchTemplate';
import NavBar from '../components/organisms/NavBar';
import PageHeader from '../components/organisms/PageHeader';
import MatchGrid from '../components/organisms/MatchGrid';
import Button from '../components/atoms/Button';
import Icon from '../components/atoms/Icon';
import { useMatchThreeWay } from '../hooks/useApi';
import { SAMPLE_TRANSACTION_ID, SAMPLE_DOCS } from '../lib/constants';

const fmtIDR = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 });

// PO/GR/Invoice shapes for MatchGrid display (keys match what organism renders)
const DISPLAY_PO      = { reference: SAMPLE_DOCS.po.reference,      quantity: SAMPLE_DOCS.po.quantity,      amount: SAMPLE_DOCS.po.amount,      currency: SAMPLE_DOCS.po.currency, npwp_vendor: SAMPLE_DOCS.po.npwp_vendor };
const DISPLAY_GR      = { reference: SAMPLE_DOCS.gr.reference,      quantity: SAMPLE_DOCS.gr.quantity,      amount: SAMPLE_DOCS.gr.amount,      currency: SAMPLE_DOCS.gr.currency };
const DISPLAY_INVOICE = {
  reference: SAMPLE_DOCS.invoice.reference,
  quantity: SAMPLE_DOCS.invoice.quantity,
  amount: SAMPLE_DOCS.invoice.amount,
  currency: SAMPLE_DOCS.invoice.currency,
  tax_invoice_ref: SAMPLE_DOCS.invoice.tax_invoice_ref,
  dpp_amount: SAMPLE_DOCS.invoice.dpp_amount,
  ppn_amount: SAMPLE_DOCS.invoice.ppn_amount,
  npwp_vendor: SAMPLE_DOCS.invoice.npwp_vendor,
};

function VerdictBanner({ matched, discrepancies }) {
  if (matched) {
    return (
      <div className="flex items-center gap-3 px-4 py-3 border border-emerald/30 bg-emerald/10">
        <span className="text-emerald shrink-0"><Icon name="check" size={16} /></span>
        <span className="text-sm font-semibold uppercase tracking-wider text-emerald">Matched</span>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2 px-4 py-3 border border-amber/30 bg-amber/10">
      <div className="flex items-center gap-3">
        <span className="text-amber shrink-0"><Icon name="alert-triangle" size={16} /></span>
        <span className="text-sm font-semibold uppercase tracking-wider text-amber">Discrepancy</span>
      </div>
      {discrepancies?.length > 0 && (
        <ul className="flex flex-col gap-1 pl-7">
          {discrepancies.map((d, i) => (
            <li key={i} className="text-sm text-[var(--color-text-inv-mute)]">· {d}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function DeltaTable({ po, invoice }) {
  const delta = po != null && invoice != null ? invoice - po : null;
  return (
    <div className="border border-[var(--border-dark)] overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border-dark)] bg-surface">
            {['Field', 'PO', 'GR', 'Invoice', 'Delta'].map((h) => (
              <th key={h} className={`${h === 'Field' ? 'text-left' : 'text-right'} px-4 py-2 text-xs font-medium uppercase tracking-wider text-[var(--color-text-inv-mute)]`}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-[var(--border-dark)] last:border-0 bg-amber/5">
            <td className="px-4 py-2 font-medium text-amber uppercase text-xs tracking-wider">DPP</td>
            <td className="px-4 py-2 text-right font-mono tabular-nums text-[var(--color-text-inv)]">{po != null ? fmtIDR.format(po) : '—'}</td>
            <td className="px-4 py-2 text-right font-mono tabular-nums text-[var(--color-text-inv-mute)]">{fmtIDR.format(SAMPLE_DOCS.gr.amount)}</td>
            <td className="px-4 py-2 text-right font-mono tabular-nums text-amber">{invoice != null ? fmtIDR.format(invoice) : '—'}</td>
            <td className="px-4 py-2 text-right font-mono tabular-nums text-sev-high">{delta != null ? (delta >= 0 ? '+' : '') + fmtIDR.format(delta) : '—'}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default function CheckerPage() {
  const [txId, setTxId] = useState(SAMPLE_TRANSACTION_ID);
  const navigate = useNavigate();
  const { data, error, loading, run } = useMatchThreeWay();

  const handleRun = useCallback(() => {
    run(txId.trim() || SAMPLE_TRANSACTION_ID, SAMPLE_DOCS).catch(() => {});
  }, [run, txId]);

  const activeTx = txId.trim() || SAMPLE_TRANSACTION_ID;

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
          <Button variant="primary" size="md" onClick={handleRun} loading={loading}>
            Run Three-Way Match
          </Button>
        </div>
      }
      resultZone={
        loading ? (
          <div className="flex items-center justify-center gap-3 py-12 text-[var(--color-text-inv-mute)]">
            <span className="inline-block w-5 h-5 rounded-full border-2 border-electric border-r-transparent animate-spin" />
            <span className="text-sm">Menjalankan three-way match…</span>
          </div>
        ) : error ? (
          <div className="flex items-start gap-3 border border-sev-critical/30 bg-sev-critical/5 px-4 py-4">
            <span className="text-sev-critical shrink-0 mt-0.5"><Icon name="x-circle" size={16} /></span>
            <div className="flex flex-col gap-2">
              <p className="text-sm text-sev-critical">{error.message}</p>
              <Button variant="ghost" size="sm" className="self-start" onClick={handleRun}>
                Retry
              </Button>
            </div>
          </div>
        ) : data ? (
          <div className="flex flex-col gap-4">
            <VerdictBanner matched={data.matched} discrepancies={data.discrepancies} />
            <MatchGrid
              po={DISPLAY_PO}
              gr={DISPLAY_GR}
              invoice={DISPLAY_INVOICE}
              differences={data.matched ? [] : ['amount', 'quantity']}
              status={data.matched ? 'matched' : 'discrepancy'}
            />
            <DeltaTable po={SAMPLE_DOCS.po.amount} invoice={SAMPLE_DOCS.invoice.dpp_amount ?? SAMPLE_DOCS.invoice.amount} />
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

import AppTemplate from '../components/templates/AppTemplate';
import NavBar from '../components/organisms/NavBar';
import PageHeader from '../components/organisms/PageHeader';
import StatStrip from '../components/organisms/StatStrip';
import VendorTable from '../components/organisms/VendorTable';
import FindingList from '../components/organisms/FindingList';
import ComingSoonGrid from '../components/organisms/ComingSoonGrid';

const SAMPLE_VENDORS = [
  { id: 1, name: 'PT Maju Jaya',      created_at: '2026-09-15', status: 'active' },
  { id: 2, name: 'CV Sentosa',        created_at: '2026-08-20', status: 'active' },
  { id: 3, name: 'PT Abadi Sejahtera',created_at: '2026-07-10', status: 'inactive' },
  { id: 4, name: 'UD Makmur',         created_at: '2026-06-05', status: 'active' },
  { id: 5, name: 'PT Nusantara',      created_at: '2026-05-01', status: 'banned' },
];

const SAMPLE_FINDINGS = [
  { id: 1, transaction_id: 'TRX-001', severity: 'high',     message: 'Harga 15% di atas benchmark pasar.',    created_at: '2026-09-30T10:00:00Z' },
  { id: 2, transaction_id: 'TRX-002', severity: 'critical', message: 'Invoice melebihi PO sebesar 8%.',       created_at: '2026-09-29T14:22:00Z' },
  { id: 3, transaction_id: 'TRX-003', severity: 'medium',   message: 'Vendor tidak terdaftar dalam whitelist.',created_at: '2026-09-28T09:15:00Z' },
  { id: 4, transaction_id: 'TRX-004', severity: 'low',      message: 'Selisih kuantitas GR vs PO sebesar 1.', created_at: '2026-09-27T16:45:00Z' },
  { id: 5, transaction_id: 'TRX-005', severity: 'high',     message: 'Approval level 2 tidak ditemukan.',     created_at: '2026-09-26T11:30:00Z' },
];

const STAT_ITEMS = [
  { value: '12',  label: 'Total Vendor' },
  { value: '48',  label: 'Total Quote' },
  { value: '7',   label: 'Open Findings' },
  { value: '72',  label: 'Risk Score' },
];

const COMING_SOON_ITEMS = [
  { icon: 'alert-triangle', title: 'Real-time Alerts',     caption: 'Notifikasi anomali real-time ke tim procurement.' },
  { icon: 'mail',           title: 'Email / Slack Alerts', caption: 'Kirim alert langsung ke email atau channel Slack.' },
  { icon: 'trending-up',    title: 'Historical Trend',     caption: 'Dashboard tren fraud historis per kuartal.' },
];

const subtitle = new Date().toLocaleString('id-ID', {
  weekday: 'long', day: '2-digit', month: 'long', year: 'numeric',
  hour: '2-digit', minute: '2-digit',
});

export default function DashboardPage() {
  return (
    <AppTemplate navbar={<NavBar activePath="/dashboard" />}>
      <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col gap-10">
        <PageHeader title="Dashboard" subtitle={subtitle} />
        <StatStrip items={STAT_ITEMS} />

        <section className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-inv-mute)]">
            Vendor Terdaftar
          </h3>
          <VendorTable rows={SAMPLE_VENDORS} />
        </section>

        <section className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-inv-mute)]">
            Temuan Terbaru
          </h3>
          <FindingList items={SAMPLE_FINDINGS} />
        </section>

        <ComingSoonGrid items={COMING_SOON_ITEMS} />
      </div>
    </AppTemplate>
  );
}

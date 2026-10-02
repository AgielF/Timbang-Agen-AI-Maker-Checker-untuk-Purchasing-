import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import WorkbenchTemplate from '../components/templates/WorkbenchTemplate';
import NavBar from '../components/organisms/NavBar';
import PageHeader from '../components/organisms/PageHeader';
import SearchBar from '../components/molecules/SearchBar';
import RecommendationPanel from '../components/organisms/RecommendationPanel';

const SAMPLE_RECOMMENDATION = {
  vendor_name: 'PT Maju Jaya',
  items: [
    {
      item_name: 'Laptop',
      recommended_vendor: 'PT Maju Jaya',
      quoted_price: 12500000,
      market_price: 13600000,
      saving_estimate: 1100000,
    },
  ],
  reason:
    'Vendor menawarkan harga 8% di bawah median pasar dengan track record pengiriman tepat waktu.',
  confidence: 0.87,
};

export default function MakerPage() {
  const [itemName, setItemName] = useState('');
  const [panelState, setPanelState] = useState('idle');
  const [result, setResult] = useState(null);
  const timerRef = useRef(null);
  const navigate = useNavigate();

  // Simulate loading → success after 3 seconds
  useEffect(() => {
    if (panelState !== 'loading') return;
    timerRef.current = setTimeout(() => {
      setResult(SAMPLE_RECOMMENDATION);
      setPanelState('success');
    }, 3000);
    return () => clearTimeout(timerRef.current);
  }, [panelState]);

  function handleSearch(query) {
    if (!query.trim()) return;
    setItemName(query.trim());
    setResult(null);
    setPanelState('loading');
  }

  function handleCancel() {
    clearTimeout(timerRef.current);
    setPanelState('idle');
    setResult(null);
  }

  function handleRetry() {
    setResult(null);
    setPanelState('loading');
  }

  function handleValidate() {
    navigate('/maker/validate?item=' + encodeURIComponent(itemName));
  }

  return (
    <WorkbenchTemplate
      navbar={<NavBar activePath="/maker" />}
      header={
        <PageHeader
          title="Maker Agent"
          badge={{ label: 'Live', variant: 'success' }}
        />
      }
      inputZone={
        <SearchBar
          placeholder="Masukkan nama item pengadaan…"
          loading={panelState === 'loading'}
          onSubmit={handleSearch}
        />
      }
      resultZone={
        <RecommendationPanel
          state={panelState}
          result={result}
          onCancel={handleCancel}
          onRetry={handleRetry}
          onValidate={handleValidate}
        />
      }
    />
  );
}

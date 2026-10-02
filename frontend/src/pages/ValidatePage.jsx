import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import WorkbenchTemplate from '../components/templates/WorkbenchTemplate';
import NavBar from '../components/organisms/NavBar';
import PageHeader from '../components/organisms/PageHeader';
import SearchBar from '../components/molecules/SearchBar';
import PriceTable from '../components/organisms/PriceTable';

const SAMPLE_QUOTES = [
  { vendor_id: 1, vendor_name: 'PT Maju Jaya', price: 11000000 },
  { vendor_id: 2, vendor_name: 'CV Sentosa',   price: 12500000 },
  { vendor_id: 3, vendor_name: 'PT Abadi',     price: 14000000 },
  { vendor_id: 4, vendor_name: 'UD Makmur',    price: 12000000 },
];

const SAMPLE_MEDIAN  = 12250000;
const SAMPLE_VERDICT = 'fair';

export default function ValidatePage() {
  const [searchParams] = useSearchParams();
  // Initialise directly from query param — no useEffect needed
  const initItem = searchParams.get('item') ?? '';
  const [query, setQuery]         = useState(initItem);
  const [showTable, setShowTable] = useState(!!initItem);

  function handleSearch(value) {
    if (!value.trim()) return;
    setQuery(value.trim());
    setShowTable(true);
  }

  return (
    <WorkbenchTemplate
      navbar={<NavBar activePath="/maker/validate" />}
      header={<PageHeader title="Price Validation" />}
      inputZone={
        <SearchBar
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Masukkan nama item…"
          onSubmit={handleSearch}
        />
      }
      resultZone={
        showTable ? (
          <PriceTable
            quotes={SAMPLE_QUOTES}
            median={SAMPLE_MEDIAN}
            verdict={SAMPLE_VERDICT}
          />
        ) : null
      }
    />
  );
}

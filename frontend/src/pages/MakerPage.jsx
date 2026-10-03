import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import WorkbenchTemplate from '../components/templates/WorkbenchTemplate';
import NavBar from '../components/organisms/NavBar';
import PageHeader from '../components/organisms/PageHeader';
import RecommendationPanel from '../components/organisms/RecommendationPanel';
import FileUploader from '../components/molecules/FileUploader';
import Button from '../components/atoms/Button';
import { useMakerRecommendation } from '../hooks/useApi';

export default function MakerPage() {
  const [itemName, setItemName] = useState('');
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const navigate = useNavigate();

  const { data, loading, error, submit } = useMakerRecommendation();

  const panelState = loading
    ? 'loading'
    : error
    ? 'error'
    : data
    ? 'success'
    : 'idle';

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault();
      if (!itemName.trim() || !file || loading) return;
      submit(itemName.trim(), file);
    },
    [itemName, file, loading, submit]
  );

  const handleRetry = useCallback(() => {
    if (!itemName.trim() || !file) return;
    submit(itemName.trim(), file);
  }, [itemName, file, submit]);

  const handleValidate = useCallback(() => {
    navigate('/maker/validate?item=' + encodeURIComponent(itemName));
  }, [navigate, itemName]);

  const handleRemoveFile = useCallback(() => {
    setFile(null);
    setFileError('');
  }, []);

  const handleFileError = useCallback((msg) => {
    setFileError(msg);
  }, []);

  const handleFileSelect = useCallback((f) => {
    setFile(f);
    setFileError('');
  }, []);

  const isDisabled = !itemName.trim() || !file || loading;

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
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Item name */}
          <div className="flex flex-col gap-1">
            <label
              htmlFor="item-name"
              className="text-sm font-medium text-[var(--color-text-inv)]"
            >
              Nama Item
            </label>
            <input
              id="item-name"
              type="text"
              value={itemName}
              onChange={(e) => setItemName(e.target.value)}
              placeholder="Masukkan nama item pengadaan…"
              disabled={loading}
              className="bg-surface border border-[var(--border-dark)] text-[var(--color-text-inv)] placeholder:text-[var(--color-text-inv-mute)] px-4 py-2 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-electric/50 disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {/* File upload */}
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-[var(--color-text-inv)]">
              Dokumen Penawaran (PDF)
            </span>
            <FileUploader
              file={file}
              onFile={handleFileSelect}
              onRemove={handleRemoveFile}
              onError={handleFileError}
              disabled={loading}
              error={fileError}
            />
          </div>

          <div className="flex justify-end">
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={isDisabled}
              loading={loading}
            >
              Get Recommendation
            </Button>
          </div>
        </form>
      }
      resultZone={
        <RecommendationPanel
          state={panelState}
          result={data}
          error={error}
          onCancel={() => {}}
          onRetry={handleRetry}
          onValidate={handleValidate}
        />
      }
    />
  );
}

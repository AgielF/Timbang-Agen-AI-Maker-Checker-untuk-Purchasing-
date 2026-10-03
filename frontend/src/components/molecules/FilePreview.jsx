import { memo } from 'react';
import Icon from '../atoms/Icon';
import Button from '../atoms/Button';

/**
 * Formats a file size in bytes to a human-readable KB or MB string.
 * @param {number} bytes
 * @returns {string}
 */
function formatSize(bytes) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${Math.round(bytes / 1024)} KB`;
}

/**
 * FilePreview — card showing the selected PDF file with a remove button.
 * Props:
 *   file      {File}       the selected file
 *   onRemove  {() => void} called when the X button is clicked
 */
function FilePreview({ file, onRemove }) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 border border-[var(--border-dark)] rounded-md bg-surface">
      {/* PDF icon */}
      <span className="text-sev-critical shrink-0">
        <Icon name="file-text" size={24} strokeWidth={1.5} />
      </span>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[var(--color-text-inv)] truncate">
          {file.name}
        </p>
        <p className="text-xs text-[var(--color-text-inv-mute)] mt-0.5">
          {formatSize(file.size)}
        </p>
      </div>

      {/* Remove button */}
      <Button
        variant="ghost"
        size="sm"
        aria-label="Hapus file"
        onClick={onRemove}
        className="shrink-0 text-[var(--color-text-inv-mute)] hover:text-sev-critical"
      >
        <Icon name="x" size={16} />
      </Button>
    </div>
  );
}

export default memo(FilePreview);

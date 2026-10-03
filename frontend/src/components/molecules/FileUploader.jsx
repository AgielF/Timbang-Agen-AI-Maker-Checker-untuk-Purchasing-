import { memo } from 'react';
import FileDropzone from './FileDropzone';
import FilePreview from './FilePreview';

/**
 * FileUploader — controlled composite: shows Dropzone when no file,
 * FilePreview when a file is selected, plus an optional error message.
 *
 * Props:
 *   file      {File|null}          currently selected file
 *   onFile    {(File) => void}     called when a valid file is picked
 *   onRemove  {() => void}         called when the file is removed
 *   onError   {(string) => void}   called on validation failure
 *   disabled  {boolean}
 *   error     {string}             error message to display below
 */
function FileUploader({ file, onFile, onRemove, onError, disabled = false, error }) {
  return (
    <div className="flex flex-col gap-2">
      {file ? (
        <FilePreview file={file} onRemove={onRemove} />
      ) : (
        <FileDropzone
          onFile={onFile}
          onError={onError}
          disabled={disabled}
        />
      )}

      {error && (
        <p className="text-xs text-sev-critical">{error}</p>
      )}
    </div>
  );
}

export default memo(FileUploader);

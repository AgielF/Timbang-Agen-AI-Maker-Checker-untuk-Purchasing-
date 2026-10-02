import { memo, useId } from 'react';
import Input from '../atoms/Input';
import Text from '../atoms/Text';

function FormField({
  label,
  error,
  hint,
  className = '',
  ...inputProps
}) {
  const id = useId();

  return (
    <div className={['flex flex-col gap-1', className].join(' ')}>
      {label && (
        <label
          htmlFor={id}
          className="text-sm font-medium text-ink"
        >
          {label}
        </label>
      )}
      <Input id={id} invalid={!!error} {...inputProps} />
      {error && (
        <Text variant="caption" className="text-sev-critical">
          {error}
        </Text>
      )}
      {!error && hint && (
        <Text variant="caption">
          {hint}
        </Text>
      )}
    </div>
  );
}

export default memo(FormField);

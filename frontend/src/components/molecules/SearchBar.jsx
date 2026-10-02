import { memo, useState } from 'react';
import Input from '../atoms/Input';
import Button from '../atoms/Button';

function SearchBar({
  value: controlledValue,
  onChange: controlledOnChange,
  onSubmit,
  loading = false,
  placeholder = 'Cari...',
  className = '',
}) {
  // Support both controlled and uncontrolled usage
  const [localValue, setLocalValue] = useState('');
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : localValue;

  function handleChange(e) {
    if (!isControlled) setLocalValue(e.target.value);
    controlledOnChange?.(e);
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit?.(value);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={['flex gap-2', className].join(' ')}
    >
      <Input
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={loading}
        className="flex-1"
      />
      <Button type="submit" loading={loading} size="md">
        Cari
      </Button>
    </form>
  );
}

export default memo(SearchBar);

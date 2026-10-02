import { forwardRef, memo } from 'react';

const Input = forwardRef(function Input(
  {
    type = 'text',
    value,
    onChange,
    placeholder,
    disabled = false,
    invalid = false,
    className = '',
    ...rest
  },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      className={[
        'w-full rounded-md px-3 py-2 text-base bg-white',
        'border transition-colors outline-none',
        'placeholder:text-[var(--color-text-mute)]',
        'focus:ring-2 focus:ring-electric/50',
        'disabled:opacity-50 disabled:pointer-events-none',
        invalid
          ? 'border-sev-critical focus:ring-sev-critical/40'
          : 'border-[var(--border-light)] focus:border-electric',
        className,
      ].join(' ')}
      aria-invalid={invalid || undefined}
      {...rest}
    />
  );
});

export default memo(Input);

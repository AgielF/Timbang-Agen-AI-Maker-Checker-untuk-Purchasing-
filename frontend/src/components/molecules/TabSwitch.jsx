import { memo } from 'react';

function TabSwitch({ tabs = [], activeId, onChange }) {
  return (
    <div
      role="tablist"
      aria-label="Checker input method"
      className="flex max-w-full overflow-x-auto border-b border-[var(--border-dark)]"
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            id={`checker-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-controls={`checker-panel-${tab.id}`}
            onClick={() => onChange(tab.id)}
            className={[
              'shrink-0 border-b-2 px-4 py-3 text-sm font-medium transition-colors',
              isActive
                ? 'border-electric text-electric'
                : 'border-transparent text-[var(--color-text-inv-mute)] hover:text-[var(--color-text-inv)]',
            ].join(' ')}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export default memo(TabSwitch);

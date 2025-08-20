import React from 'react';
import Logo from './Logo';
import { IconSettings } from './Icons';

function MobileHeader({ onNew, onOpenSettings }) {
  return (
    <div className="w-full bg-black/80 backdrop-blur-sm text-white p-3 flex items-center justify-between fixed top-0 left-0 z-30">
      <div className="flex items-center gap-2">
        <Logo small />
      </div>
      <div className="flex items-center gap-3">
        <button onClick={onOpenSettings} aria-label="Settings" className="p-2 rounded-md">
          <IconSettings />
        </button>
        <button onClick={onNew} className="bg-yellow-400/95 text-black px-3 py-2 rounded-lg font-semibold shadow">New</button>
      </div>
    </div>
  );
}

export default MobileHeader;
import React from 'react';
import Logo from './Logo';
import { IconSettings } from './Icons';
import { Button } from '@blueprintjs/core';
import { Cog } from '@blueprintjs/icons';

function MobileHeader({ onNew, onOpenSettings }) {
  return (
    <div className="w-full bg-background/80 backdrop-blur-sm text-text-dark p-3 flex items-center justify-between fixed top-0 left-0 z-30">
      <div className="flex items-center gap-2">
        <Logo small />
      </div>
      <div className="flex items-center gap-3">
        <Button onClick={onOpenSettings} aria-label="Settings" icon={<Cog />} minimal />
        <Button onClick={onNew} intent="primary" text="New" />
      </div>
    </div>
  );
}

export default MobileHeader;
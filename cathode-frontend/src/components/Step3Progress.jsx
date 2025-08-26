import React from 'react';
import { Button, ProgressBar } from '@blueprintjs/core';
import Logo from './Logo';

function Step3Progress({ progress, onBack, onCancel }) {
  return (
    <div className="pt-20 px-4 pb-40 flex flex-col items-center">
      <Logo small />
      <div className="mt-6 w-full">
        <div className="text-text-dark">Searching lyrics & scoring songs</div>
        <ProgressBar value={progress / 100} />
        <div className="bp6-text-muted text-sm mt-2">
          {Math.round(progress)}% — ~{Math.max(0, 3 - Math.floor(progress / 40))} mins remaining
        </div>
        <div className="flex justify-between mt-6">
          <Button onClick={onBack} text="Back" minimal />
          <Button onClick={onCancel} text="Cancel" minimal />
        </div>
      </div>
    </div>
  );
}

export default Step3Progress;
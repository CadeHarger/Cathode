import React, { useState } from 'react';
import { Button, Collapse } from '@blueprintjs/core';
import { IconSpotify } from './Icons';
import { formatDuration } from '../utils/helpers';
import { ChevronDown, ChevronUp } from '@blueprintjs/icons';

function SongCard({ s }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bp6-card bp6-elevation-1 p-3 rounded-xl mb-3">
      <div className="flex items-center gap-3">
        <div className="w-14 h-14 bg-slate-300 rounded"></div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-text-dark font-semibold">{s.title}</div>
              <div className="bp6-text-muted text-sm">{s.artist}</div>
            </div>
            <div className="bp6-text-muted text-sm">{s.score ? `${Math.round(s.score * 100)}%` : ''}</div>
          </div>
          <div className="bp6-text-muted text-xs mt-2">{formatDuration(s.duration_ms)}</div>
        </div>
      </div>
      <Collapse isOpen={open}>
        <div className="mt-3 border-t border-slate-300 pt-3 text-slate-500 text-sm">
          <div className="mb-2">Album: {s.album}</div>
          <div className="mb-2">Streams: {s.streams ?? '—'}</div>
          <div className="flex gap-3 mt-2">
            <Button icon={<IconSpotify />} text="Open" minimal />
            <Button text="More" minimal />
          </div>
        </div>
      </Collapse>
      <div className="mt-2 text-right">
        <Button onClick={() => setOpen((v) => !v)} minimal icon={open ? <ChevronUp /> : <ChevronDown />} text={open ? 'Collapse' : 'Details'} />
      </div>
    </div>
  );
}

export default SongCard;
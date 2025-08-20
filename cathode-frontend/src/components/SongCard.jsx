import React, { useState } from 'react';
import { IconSpotify } from './Icons';
import { formatDuration } from '../utils/helpers';

function SongCard({ s }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-slate-900/60 p-3 rounded-xl mb-3">
      <div className="flex items-center gap-3">
        <div className="w-14 h-14 bg-slate-700 rounded"></div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-semibold">{s.title}</div>
              <div className="text-slate-400 text-sm">{s.artist}</div>
            </div>
            <div className="text-slate-400 text-sm">{s.score ? `${Math.round(s.score * 100)}%` : ''}</div>
          </div>
          <div className="text-slate-400 text-xs mt-2">{formatDuration(s.duration_ms)}</div>
        </div>
      </div>
      {open && (
        <div className="mt-3 border-t border-slate-800 pt-3 text-slate-300 text-sm">
          <div className="mb-2">Album: {s.album}</div>
          <div className="mb-2">Streams: {s.streams ?? '—'}</div>
          <div className="flex gap-3 mt-2">
            <button className="flex items-center gap-2 px-3 py-2 rounded bg-slate-800"> <IconSpotify /> Open</button>
            <button className="px-3 py-2 rounded border border-slate-700">More</button>
          </div>
        </div>
      )}
      <div className="mt-2 text-right">
        <button onClick={() => setOpen((v) => !v)} className="text-slate-400 text-sm">{open ? 'Collapse' : 'Details'}</button>
      </div>
    </div>
  );
}

export default SongCard;
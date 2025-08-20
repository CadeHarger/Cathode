import React from 'react';
import { Button } from '@blueprintjs/core';
import { Export, Share } from '@blueprintjs/icons';
import SongCard from '../components/SongCard';

function ResultsView({ playlist, onBack }) {
  if (!playlist) return null;
  return (
    <div className="pt-20 px-4 pb-40">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-slate-500 text-xs">Prompt</div>
          <div className="text-text-dark font-bold text-lg truncate">{playlist.title}</div>
        </div>
        <div>
          <Button icon={<Export />} minimal text="Export" />
        </div>
      </div>

      <div>
        {playlist.songs.map((s) => (
          <SongCard key={s.id} s={s} />
        ))}
      </div>

      <div className="fixed bottom-6 left-4 right-4">
        <div className="bg-gradient-to-r from-slate-200/80 to-slate-200/50 rounded-xl p-3 flex items-center justify-between">
          <div>
            <div className="text-slate-500 text-xs">Playlist</div>
            <div className="text-text-dark font-semibold">{playlist.title}</div>
          </div>
          <div className="flex items-center gap-3">
            <Button intent="primary" text="Open in Spotify" icon={<Share />} />
          </div>
        </div>
      </div>

    </div>
  );
}

export default ResultsView;
import React from 'react';
import SongCard from '../components/SongCard';

function ResultsView({ playlist, onBack }) {
  if (!playlist) return null;
  return (
    <div className="pt-20 px-4 pb-40">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-slate-300 text-xs">Prompt</div>
          <div className="text-white font-bold text-lg truncate">{playlist.title}</div>
        </div>
        <div>
          <button className="px-3 py-2 rounded bg-slate-800 text-slate-300">Export</button>
        </div>
      </div>

      <div>
        {playlist.songs.map((s) => (
          <SongCard key={s.id} s={s} />
        ))}
      </div>

      <div className="fixed bottom-6 left-4 right-4">
        <div className="bg-gradient-to-r from-slate-900/80 to-slate-900/50 rounded-xl p-3 flex items-center justify-between">
          <div>
            <div className="text-slate-400 text-xs">Playlist</div>
            <div className="text-white font-semibold">{playlist.title}</div>
          </div>
          <div className="flex items-center gap-3">
            <button className="px-4 py-2 rounded bg-yellow-400 font-semibold">Open in Spotify</button>
          </div>
        </div>
      </div>

    </div>
  );
}

export default ResultsView;
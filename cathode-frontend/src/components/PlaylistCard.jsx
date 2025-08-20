import React from 'react';

function PlaylistCard({ p, onOpen }) {
  return (
    <div onClick={() => onOpen(p.id)} className="bg-slate-900/70 p-3 rounded-xl shadow-md mb-3 cursor-pointer">
      <div className="flex items-center gap-3">
        <div className="grid grid-cols-2 gap-1 w-16 h-16">
          {/* show up to 4 covers */}
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className={`bg-slate-700 rounded ${i === 0 ? 'col-span-2 row-span-2' : ''}`}></div>
          ))}
        </div>
        <div className="flex-1">
          <div className="text-white font-semibold">{p.title}</div>
          <div className="text-slate-400 text-sm mt-1">{p.songs?.length ?? 0} songs • {p.tagline ?? 'Cathartic mix'}</div>
        </div>
        <div className="text-slate-400">▾</div>
      </div>
    </div>
  );
}

export default PlaylistCard;
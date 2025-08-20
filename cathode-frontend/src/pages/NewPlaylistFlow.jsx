import React, { useEffect, useState } from 'react';
import Logo from '../components/Logo';
import { API_CREATE_PLAYLIST } from '../utils/helpers';

function NewPlaylistFlow({ onCancel, onCreated }) {
  const [step, setStep] = useState(1);
  const [prompt, setPrompt] = useState('');
  const [filters, setFilters] = useState({ genres: [] });
  const [progress, setProgress] = useState(0);
  const [isCreating, setCreating] = useState(false);

  useEffect(() => {
    let t;
    if (isCreating && progress < 100) {
      t = setInterval(() => setProgress((p) => Math.min(100, p + Math.random() * 12)), 400);
    }
    return () => clearInterval(t);
  }, [isCreating, progress]);

  async function handleCreate() {
    setCreating(true);
    setProgress(5);
    try {
      // Integrate with your backend
      // const res = await fetch(API_CREATE_PLAYLIST, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ prompt, filters }),
      // });
      // const data = await res.json();

      // For quick demo, we fake a response
      await new Promise((r) => setTimeout(r, 1200));
      setProgress(65);
      await new Promise((r) => setTimeout(r, 900));
      setProgress(95);
      await new Promise((r) => setTimeout(r, 400));

      const data = {
        id: Date.now().toString(),
        title: prompt.slice(0, 30) || 'Untitled playlist',
        songs: Array.from({ length: 8 }).map((_, i) => ({
          id: `s-${i}`,
          title: `Song ${i + 1}`,
          artist: `Artist ${i + 1}`,
          duration_ms: 180000 + i * 10000,
          score: Math.random(),
          album: 'Album X',
          streams: Math.floor(Math.random() * 1e6),
        })),
      };

      setProgress(100);
      setCreating(false);
      onCreated(data);
    } catch (err) {
      console.error(err);
      setCreating(false);
      alert('Failed to create playlist — check your connection.');
    }
  }

  if (step === 1)
    return (
      <div className="pt-20 px-4 pb-40">
        <h2 className="text-white font-bold text-xl mb-2">Describe the experience</h2>
        <p className="text-slate-400 text-sm mb-4">Write a few lines about what happened and how you felt. Be honest — it helps the playlist resonate.</p>
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={6} className="w-full rounded-lg p-3 bg-slate-800 text-white placeholder-slate-400" placeholder="I had my heart broken but it's also a relief..." />
        <div className="flex justify-between items-center mt-4">
          <button onClick={onCancel} className="text-slate-400">Cancel</button>
          <button onClick={() => setStep(2)} className="bg-yellow-400 px-4 py-2 rounded font-semibold">Next</button>
        </div>
      </div>
    );

  if (step === 2) {
    return (
      <div className="pt-20 px-4 pb-40">
        <h2 className="text-white font-bold text-xl mb-2">Select filters</h2>
        <p className="text-slate-400 text-sm mb-4">Pick a genre or mood to bias the playlist.</p>
        <div className="flex gap-2 flex-wrap">
          {['Indie', 'Pop', 'R&B', 'Rock', 'All'].map((g) => (
            <button key={g} onClick={() => setFilters((f) => ({ ...f, genres: [g] }))} className={`px-3 py-2 rounded ${filters.genres.includes(g) ? 'bg-slate-100 text-black' : 'bg-slate-800 text-slate-300'}`}>
              {g}
            </button>
          ))}
        </div>
        <div className="mt-6">
          <label className="text-slate-400 text-sm">Exploration slider</label>
          <input type="range" min={0} max={100} className="w-full mt-2" />
        </div>
        <div className="flex justify-between items-center mt-6">
          <button onClick={() => setStep(1)} className="text-slate-400">Back</button>
          <button onClick={() => { setStep(3); handleCreate(); }} className="bg-yellow-400 px-4 py-2 rounded font-semibold">Create</button>
        </div>
      </div>
    );
  }

  // Step 3: waiting / progress
  return (
    <div className="pt-20 px-4 pb-40 flex flex-col items-center">
      <Logo small />
      <div className="mt-6 w-full">
        <div className="text-slate-300">Searching lyrics & scoring songs</div>
        <div className="w-full bg-slate-800 rounded-full h-3 mt-3 overflow-hidden">
          <div className="h-full bg-yellow-400 transition-all" style={{ width: `${progress}%` }} />
        </div>
        <div className="text-slate-400 text-sm mt-2">{Math.round(progress)}% — ~{Math.max(0, 3 - Math.floor(progress / 40))} mins remaining</div>
        <div className="flex justify-between mt-6">
          <button onClick={() => { setStep(2); }} className="text-slate-400">Back</button>
          <button onClick={() => { setStep(1); setProgress(0); }} className="text-slate-400">Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default NewPlaylistFlow;
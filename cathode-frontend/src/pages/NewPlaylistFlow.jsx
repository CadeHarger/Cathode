import React, { useEffect, useState } from 'react';
import Logo from '../components/Logo';
import { API_CREATE_PLAYLIST } from '../utils/helpers';
import { Button, TextArea, ButtonGroup, Slider, ProgressBar } from '@blueprintjs/core';

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
        <h2 className="bp6-heading text-text-dark font-bold text-xl mb-2">Describe the experience</h2>
        <p className="bp6-text-muted text-sm mb-4">Write a few lines about what happened and how you felt. Be honest — it helps the playlist resonate.</p>
        <TextArea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={6} className="w-full rounded-lg p-3 bg-slate-200 text-text-dark placeholder-slate-500" placeholder="I had my heart broken but it's also a relief..." fill />
        <div className="flex justify-between items-center mt-4">
          <Button onClick={onCancel} text="Cancel" minimal />
          <Button onClick={() => setStep(2)} intent="primary" text="Next" />
        </div>
      </div>
    );

  if (step === 2) {
    return (
      <div className="pt-20 px-4 pb-40">
        <h2 className="bp6-heading text-text-dark font-bold text-xl mb-2">Select filters</h2>
        <p className="bp6-text-muted text-sm mb-4">Pick a genre or mood to bias the playlist.</p>
        <ButtonGroup>
          {['Indie', 'Pop', 'R&B', 'Rock', 'All'].map((g) => (
            <Button key={g} onClick={() => setFilters((f) => ({ ...f, genres: [g] }))} active={filters.genres.includes(g)} text={g} />
          ))}
        </ButtonGroup>
        <div className="mt-6">
          <label className="bp6-label text-sm">Exploration slider</label>
          <Slider min={0} max={100} />
        </div>
        <div className="flex justify-between items-center mt-6">
          <Button onClick={() => setStep(1)} text="Back" minimal />
          <Button onClick={() => { setStep(3); handleCreate(); }} intent="primary" text="Create" />
        </div>
      </div>
    );
  }

  // Step 3: waiting / progress
  return (
    <div className="pt-20 px-4 pb-40 flex flex-col items-center">
      <Logo small />
      <div className="mt-6 w-full">
        <div className="text-text-dark">Searching lyrics & scoring songs</div>
        <ProgressBar value={progress / 100} />
        <div className="bp6-text-muted text-sm mt-2">{Math.round(progress)}% — ~{Math.max(0, 3 - Math.floor(progress / 40))} mins remaining</div>
        <div className="flex justify-between mt-6">
          <Button onClick={() => { setStep(2); }} text="Back" minimal />
          <Button onClick={() => { setStep(1); setProgress(0); }} text="Cancel" minimal />
        </div>
      </div>
    </div>
  );
}

export default NewPlaylistFlow;
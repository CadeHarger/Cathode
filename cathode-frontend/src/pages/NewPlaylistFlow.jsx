import React, { useEffect, useState } from 'react';
import { API_CREATE_PLAYLIST } from '../utils/helpers';
import Step1DescribeExperience from './Step1DescribeExperience';
import Step2SelectFilters from './Step2SelectFilters';
import Step3Progress from './Step3Progress';

function NewPlaylistFlow({ onCancel, onCreated }) {
  const [step, setStep] = useState(1);
  const [prompt, setPrompt] = useState('');
  const [filters, setFilters] = useState({ genres: [], exploration: 3 });
  const [progress, setProgress] = useState(0);
  const [isCreating, setCreating] = useState(false);

  useEffect(() => {
    let t;
    if (isCreating && progress < 100) {
      t = setInterval(() => setProgress(10));// ((p) => Math.min(100, p + Math.random() * 12)), 400);
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

  if (step === 1) {
    return (
      <Step1DescribeExperience 
        prompt={prompt}
        setPrompt={setPrompt}
        onCancel={onCancel}
        onNext={() => setStep(2)}
      />
    );
  }

  if (step === 2) {
    return (
      <Step2SelectFilters 
        filters={filters}
        setFilters={setFilters}
        onBack={() => setStep(1)}
        onCreatePlaylist={() => { setStep(3); handleCreate(); }}
        onCancel={onCancel}
      />
    );
  }

  // Step 3: waiting / progress
  return (
    <Step3Progress 
      progress={progress}
      onBack={() => setStep(2)}
      onCancel={() => { setStep(1); setProgress(0); }}
    />
  );
}

export default NewPlaylistFlow;
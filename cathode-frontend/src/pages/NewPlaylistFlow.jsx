import React, { useEffect, useState } from 'react';
import { useCreatePlaylist, useJobPolling } from '../hooks/useJobPolling';
import Step1DescribeExperience from './Step1DescribeExperience';
import Step2SelectFilters from './Step2SelectFilters';
import Step3Progress from './Step3Progress';

function NewPlaylistFlow({ onCancel, onCreated, onHome, onAbout }) {
  const [step, setStep] = useState(1);
  const [prompt, setPrompt] = useState('');
  const [filters, setFilters] = useState({ genres: [], exploration: 3 });
  const [jobId, setJobId] = useState(null);
  
  // Hooks for playlist creation and polling
  const { createPlaylist, isCreating, error: createError } = useCreatePlaylist();
  const { 
    progress, 
    status, 
    message, 
    result, 
    isCompleted, 
    isFailed, 
    error: pollingError,
    hasTimedOut 
  } = useJobPolling(jobId);

  // Handle job completion
  useEffect(() => {
    if (isCompleted && result) {
      onCreated(result);
    }
  }, [isCompleted, result, onCreated]);

  // Handle job failure
  useEffect(() => {
    if (isFailed || hasTimedOut) {
      const errorMsg = pollingError || createError || 'Failed to create playlist';
      alert(`${errorMsg} — please try again.`);
      setStep(2); // Go back to step 2
      setJobId(null);
    }
  }, [isFailed, hasTimedOut, pollingError, createError]);

  async function handleCreate() {
    try {
      const newJobId = await createPlaylist(prompt, filters);
      setJobId(newJobId);
    } catch (err) {
      console.error('Failed to start playlist creation:', err);
      alert('Failed to start playlist creation — check your connection.');
    }
  }

  if (step === 1) {
    return (
      <Step1DescribeExperience 
        prompt={prompt}
        setPrompt={setPrompt}
        onCancel={onCancel}
        onNext={() => setStep(2)}
        onHome={onHome}
        onAbout={onAbout}
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
        onHome={onHome}
        onAbout={onAbout}
      />
    );
  }

  // Step 3: waiting / progress
  return (
    <Step3Progress 
      progress={progress}
      message={message}
      status={status}
      isCreating={isCreating}
      onBack={() => setStep(2)}
      onCancel={() => { 
        setStep(1); 
        setJobId(null);
      }}
      onHome={onHome}
      onAbout={onAbout}
    />
  );
}

export default NewPlaylistFlow;
import React, { useState, useEffect } from 'react';
import { Button, ProgressBar } from '@blueprintjs/core';
import Logo from '../components/Logo';
import StepHeader from '../components/StepHeader';
import BottomBar from '../components/BottomBar';

import './styles/steps.css';

function Step3Progress({ progress, onBack, onCancel }) {
  const [searchedSongs, setSearchedSongs] = useState(0);
  
  // Calculate songs searched based on progress (simulate backend data)
  useEffect(() => {
    // Simulate searching through a large catalog of songs
    const totalSongs = 50000; // Example total song count
    const currentSongs = Math.floor((progress / 100) * totalSongs);
    setSearchedSongs(currentSongs);
  }, [progress]);

  return (
    <div className="container">
      <StepHeader 
        stepNumber={3}
        title="Generating Your Playlist"
        subtitle="We're analyzing lyrics and scoring songs to create the perfect playlist for your experience."
        onCancel={onCancel}
      />
      
      <div className="middle-section-3">
        <div className="progress-container">
          {/* Large Progress Bar */}
          <div className="progress-bar-container">
            <ProgressBar 
              value={progress / 100} 
              className="large-progress-bar"
              animate={true}
            />
          </div>
          
          {/* Progress Text */}
          <div className="progress-text-container">
            <div className="progress-percentage">
              {Math.round(progress)}%
            </div>
            <div className="progress-details">
              Searching {searchedSongs.toLocaleString()} songs...
            </div>
            <div className="progress-time">
              ~{Math.max(0, 3 - Math.floor(progress / 40))} mins remaining
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center mt-4">
        <Button onClick={onBack} text="Back" variant="minimal" size="large"/>
        <Button onClick={onCancel} text="Cancel" variant="minimal" size="large"/>
      </div>
      
      <BottomBar />
    </div>
  );
}

export default Step3Progress;

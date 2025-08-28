import React, { useState, useEffect } from 'react';
import { Button, ProgressBar } from '@blueprintjs/core';
import StepHeader from '../components/StepHeader';
import BottomBar from '../components/BottomBar';
import './styles/steps.css';


const puns = [
  "Get Amped",
  "Charging up",
  "Finding shocking results",
  "Hiring music conductors",
  "Sorry for the watt",
]

function Step3Progress({ progress = 0, message = '', status = 'pending', isCreating = false, onBack, onCancel, onHome, onAbout }) {
  const [punIndex, setPunIndex] = useState(0);
  const [searchedSongs, setSearchedSongs] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  
  // Calculate songs searched based on progress (simulate backend data)
  useEffect(() => {
    // Simulate searching through a large catalog of songs
    const totalSongs = 50000; // Example total song count
    const currentSongs = Math.floor((progress / 100) * totalSongs);
    setSearchedSongs(currentSongs);
  }, [progress]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setIsAnimating(true);
      
      // After exit animation completes, change the pun and trigger entrance animation
      setTimeout(() => {
        setPunIndex((prevIndex) => (prevIndex + 1) % puns.length);
        setIsAnimating(false);
      }, 400); // Match the exit animation duration
    }, 5000); // Rotate every 5 seconds

    return () => clearInterval(intervalId); // Cleanup on unmount
  }, []);

  const currentMessage = `We're analyzing lyrics and scoring songs to create the perfect playlist for your experience.`;

  return (
    <div className="container">
      <StepHeader 
        stepNumber="3" 
        title={"Getting Results..."} 
        subtitle={currentMessage} 
        onCancel={onCancel} 
      />
      <h1>
        {status === 'failed' ? 'Failure!' : (
          <div className="pun-container">
            <span className={`pun-text ${isAnimating ? 'exiting' : ''}`} key={punIndex}>
              {puns[punIndex]}...
            </span>
          </div>
        )}
      </h1>
      
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
              {message || `Searching ${searchedSongs.toLocaleString()} songs...`}
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
      
      <BottomBar onHome={onHome} onAbout={onAbout} />
    </div>
  );
}

export default Step3Progress;

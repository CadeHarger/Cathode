import React, { useState, useEffect } from 'react';
import { ProgressBar } from '@blueprintjs/core';
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

function Step3Progress({ progress = 0, message = '', status = 'pending', isCreating = false, jobId, initialSongCount = 0, cancelJob, onBack, onCancel, onHome, onAbout }) {

  const handleHomeWarning = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to go home? This will cancel your current playlist creation.'
    );
    if (confirmed) {
      // Cancel the job if it exists and is running
      if (jobId && cancelJob) {
        try {
          const cancelled = await cancelJob();
          if (cancelled) {
            console.log('Job cancelled successfully');
          }
        } catch (error) {
          console.error('Failed to cancel job:', error);
        }
      }
      onHome();
    }
  };
  
  const [punIndex, setPunIndex] = useState(0);
  const [searchedSongs, setSearchedSongs] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [searchStats, setSearchStats] = useState([]);
  const [currentSongCount, setCurrentSongCount] = useState(initialSongCount);
  
  // Extract song counts from backend messages
  useEffect(() => {
    if (message) {
      // Extract numbers from messages like "Found 1,245 candidate songs from Spotify"
      const numberMatch = message.match(/(\d{1,3}(?:,\d{3})*|\d+)/);
      if (numberMatch && (message.includes('songs') || message.includes('candidates'))) {
        const count = parseInt(numberMatch[1].replace(/,/g, ''), 10);
        setCurrentSongCount(count);
      }
    }
  }, [message]);

  // Track search statistics from backend messages
  useEffect(() => {
    if (message && message !== searchStats[searchStats.length - 1]) {
      // Check if this is a statistics message (contains numbers and keywords)
      if (message.includes('songs') || message.includes('candidates') || message.includes('dataset')) {
        setSearchStats(prevStats => {
          // Avoid duplicates
          if (!prevStats.includes(message)) {
            return [...prevStats.slice(-3), message]; // Keep only last 4 items
          }
          return prevStats;
        });
      }
    }
  }, [message, searchStats]);

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
              {puns[punIndex]} ...
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
              {currentSongCount > 0 ? `Searching ${currentSongCount.toLocaleString()} songs...` : (message || "Initializing search...")}
            </div>
            <div className="progress-time">
              ~{Math.max(0, 3 - Math.floor(progress / 40))} mins remaining
            </div>
          </div>
        </div>
      </div>
      <BottomBar onHome={onHome} onAbout={onAbout} onHomeWarning={handleHomeWarning} />
    </div>
  );
}

export default Step3Progress;

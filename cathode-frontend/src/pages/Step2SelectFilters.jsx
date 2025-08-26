import React from 'react';
import { Button, ButtonGroup, Slider } from '@blueprintjs/core';
import StepHeader from '../components/StepHeader';
import BottomBar from '../components/BottomBar';
import './styles/steps.css';


const externalToInternal = {
  'Pop': 'pop',
  'Rap': 'rap',
  'R&B': 'rb',
  'Rock': 'rock',
  'Country': 'country',
}


function Step2SelectFilters({ filters, setFilters, onBack, onCreatePlaylist, onCancel, onHome, onAbout }) {
  const genres = ['acoustic', 'rock', 'pop', 'hip-hop', 'electronic', 'jazz', 'blues', 'classical'];

  const toggleGenre = (genre) => {
    setFilters((f) => ({
      ...f,
      genres: f.genres.includes(genre)
        ? f.genres.filter(g => g !== genre)
        : [...f.genres, genre]
    }));
  };

  return (
    <div className="container">
      <StepHeader 
        stepNumber="2."
        title="Select Filters"
        subtitle="Decide how the playlist should be generated."
        onCancel={onCancel}
      />
      <div className="middle-section-2">
        <div className="filters">
          <div className="filter">
            <h3>1. Genres</h3>
            <p className="bp6-text-muted text-sm mb-4">Pick genres to include in the playlist.</p>
            <ButtonGroup>
              {['Pop', 'Rap', 'R&B', 'Rock', 'Country', 'Misc'].map((g) => (
                <Button 
                  key={g} 
                  onClick={() => setFilters((f) => ({
                    ...f, 
                    genres: f.genres.includes(g) 
                      ? f.genres.filter(genre => genre !== g)
                      : [...f.genres, g]
                  }))} 
                  active={filters.genres.includes(g)} 
                  text={g} 
                />
              ))}
              <Button 
                className={`all-button ${filters.genres.length === 0 ? 'all-button-active' : ''}`}
                onClick={() => setFilters((f) => ({ ...f, genres: [] }))} 
                text="All" 
              />
            </ButtonGroup>
          </div>
          <div className="filter">
            <h3>2. Exploration</h3>
            <p className="bp6-text-muted text-sm mb-4">More exploration = more variety, less popular songs.</p>
            <div style={{marginLeft: '3px', width: '100%', marginRight: '3px'}}>
            <Slider 
              min={0} 
              max={10} 
              value={filters.exploration} 
              onChange={(value) => setFilters((f) => ({ ...f, exploration: value }))}
            />
            </div>
          </div>
        </div>
        <div className="flex justify-between items-center mt-6">
          <Button onClick={onBack} text="Back" minimal />
          <Button onClick={onCreatePlaylist} intent="primary" text="Create" />
        </div>
      </div>
      <BottomBar onHome={onHome} onAbout={onAbout} />
    </div>
  );
}

export default Step2SelectFilters;
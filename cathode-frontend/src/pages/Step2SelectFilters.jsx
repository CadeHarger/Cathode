import React from 'react';
import { Button, ButtonGroup, Slider } from '@blueprintjs/core';
import Logo from '../components/Logo';
import { Home } from '@blueprintjs/icons';


const externalToInternal = {
  'Pop': 'pop',
  'Rap': 'rap',
  'R&B': 'rb',
  'Rock': 'rock',
  'Country': 'country',
}


function Step2SelectFilters({ filters, setFilters, onBack, onCreatePlaylist, onCancel }) {
  return (
    <div className="container">
      <div className="top-section-1">
        <div className="logo-1">
          <Logo />
        </div>
        <div className="flex flex-col items-center justify-center">
          <h1 className="bp6-heading text-text-dark font-bold text-xl mb-2">Select Filters</h1>
          <p className="bp6-text-muted text-sm mb-4">Decide how the playlist should be generated.</p>
        </div>
        <div className="home-1">
          <Home onClick={onCancel} size={30} className="home-icon" />
        </div>
      </div>
      <div className="middle-section-2">
        <div className="filter">
          <h3>1. Genres</h3>
          <p className="bp6-text-muted text-sm mb-4">Pick genres to include in the playlist.</p>
          <ButtonGroup>
            {['Pop', 'Rap', 'R&B', 'Rock', 'Country', 'Misc', 'All'].map((g) => (
              <Button 
                key={g} 
                onClick={() => setFilters((f) => ({ ...f, genres: [g] }))} 
                active={filters.genres.includes(g)} 
                text={g} 
              />
            ))}
          </ButtonGroup>
        </div>
        <div className="mt-6">
          <label className="bp6-label text-sm">Exploration slider</label>
          <Slider min={0} max={100} />
        </div>
        <div className="flex justify-between items-center mt-6">
          <Button onClick={onBack} text="Back" minimal />
          <Button onClick={onCreatePlaylist} intent="primary" text="Create" />
        </div>
      </div>
    </div>
  );
}

export default Step2SelectFilters;
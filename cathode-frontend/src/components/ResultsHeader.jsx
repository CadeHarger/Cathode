import React, { useState, useEffect } from 'react';
import { Home } from '@blueprintjs/icons';
import Logo from './Logo';
import { isMobile } from '../utils/helpers';
import '../pages/styles/steps.css';

function ResultsHeader({ playlist, onBack, onExport }) {
  const [isMobileDevice, setIsMobileDevice] = useState(false);

  useEffect(() => {
    setIsMobileDevice(isMobile());
  }, []);

  return (
    <div className="top-section-2">
      {!isMobileDevice && (
        <div className="logo-1">
          <Logo animated={false} />
        </div>
      )}
      <div className="flex flex-col items-center justify-center height-100">
        <h1 className="bp6-heading text-text-dark font-bold text-xl mb-2">
          <div className="flex flex-row items-center justify-center gap-20">
            <div className="results-icon-container">
              <div className="results-icon-trail"></div>
              <span className="results-icon">🎵</span>
            </div>
            Your Playlist is Ready!
          </div>
        </h1>
        <p className="bp6-text-muted text-center">
          {playlist?.songs?.length || 0} songs curated for "{playlist?.title || 'your experience'}"
        </p>
      </div>
      {!isMobileDevice && (
        <div className="home-1">
          <Home onClick={onBack} size={30} className="home-icon" />
        </div>
      )}
    </div>
  );
}

export default ResultsHeader;

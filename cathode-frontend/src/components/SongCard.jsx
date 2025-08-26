import React, { useState } from 'react';
import { Button, Collapse } from '@blueprintjs/core';
import { formatDuration } from '../utils/helpers';
import SpotifyIcon from '../assets/Spotify-Icon.png';
import './SongCard.css';

function SongCard({ s }) {
  const [open, setOpen] = useState(false);

  const handleCardClick = () => {
    setOpen((v) => !v);
  };

  const handleSpotifyClick = (e) => {
    e.stopPropagation(); // Prevent card click when clicking Spotify button
    // TODO: Implement Spotify functionality
    console.log('Open in Spotify:', s);
  };

  return (
    <div className="song-card-wrapper" onClick={handleCardClick}>
      <div className="album-cover"></div>
      <div className="bp6-card bp6-elevation-1 song-card">
        <div className="song-main-content">
          <div className="song-content-inner">
            <div className="song-details-row">
              <div className="song-info">
                <div className="song-title">{s.title}</div>
                <div className="song-artist">{s.artist}</div>
                <div className="song-duration">{formatDuration(s.duration_ms)}</div>
              </div>
              <div className="song-score">{s.score ? `${Math.round(s.score * 100)}%` : ''}</div>
            </div>
          </div>
        </div>
        
        <Collapse isOpen={open}>
          <div className="song-details-collapse">
            <div className="detail-row">Album: {s.album}</div>
            <div className="detail-row">Streams: {s.streams?.toLocaleString() ?? '—'}</div>
            <div className="song-details-actions">
              <Button 
                icon={<img src={SpotifyIcon} alt="Spotify" className="spotify-icon" />} 
                text="Open in Spotify" 
                minimal 
                onClick={handleSpotifyClick}
              />
            </div>
          </div>
        </Collapse>

      </div>
    </div>
  );
}

export default SongCard;
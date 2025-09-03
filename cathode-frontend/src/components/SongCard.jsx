import React, { useState, useRef } from 'react';
import { Button, Collapse } from '@blueprintjs/core';
import { formatDuration } from '../utils/helpers';
import SpotifyIcon from '../assets/Spotify-Icon.png';
import './SongCard.css';

function SongCard({ s, skeleton = false }) {
  const [open, setOpen] = useState(false);
  const imgRef = useRef(null);

  const handleCardClick = () => {
    if (skeleton) return; // Prevent interaction when in skeleton mode
    setOpen((v) => !v);
  };

  const handleSpotifyClick = (e) => {
    e.stopPropagation(); // Prevent card click when clicking Spotify button
    // TODO: Implement Spotify functionality
    window.open(s.url, '_blank');
    console.log('Open in Spotify:', s);
  };

  if (skeleton) {
    return (
      <div className="song-card-wrapper">
        <div className="album-cover bp6-skeleton"></div>
        <div className="bp6-card bp6-elevation-1 song-card">
          <div className="song-main-content">
            <div className="song-content-inner">
              <div className="song-details-row">
                <div className="song-info">
                  <div className="song-title bp6-skeleton"></div>
                  <div className="song-artist bp6-skeleton"></div>
                  <div className="song-duration bp6-skeleton"></div>
                </div>
                <div className="song-score bp6-skeleton"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="song-card-wrapper" onClick={handleCardClick}>
      <div className="album-cover">
        {s?.image_url ? (
          <img
            ref={imgRef}
            src={s.image_url}
            alt={`${s.title} album cover`}
            className="album-cover-img"
            onError={(e) => {
              if (e.currentTarget) {
                e.currentTarget.style.display = 'none';
              }
            }}
          />
        ) : null}
      </div>
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
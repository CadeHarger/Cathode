import React from 'react';
import './PlaylistCard.css';

function PlaylistCard({ p, onOpen, skeleton = false }) {

  const formatGenres = (genres) => {
    if (!genres || genres.length === 0) return 'Various Genres';
    return genres.slice(0, 3).join(', ');
  };

  console.log(p);

  return (
    <div className="playlist-card-wrapper" onClick={skeleton ? undefined : () => onOpen(p.id)}>
      <div className="playlist-cover">
        <div className="playlist-cover-grid">
          {Array.from({ length: 4 }).map((_, i) => (
            <div 
              key={i} 
              className={`${skeleton ? 'bp6-skeleton' : 'playlist-cover-tile'} ${i === 0 ? 'tile-large' : ''}`}
            />
          ))}
        </div>
      </div>
      <div className="bp6-card bp6-elevation-1 playlist-card">
        <div className="playlist-main-content">
          <div className="playlist-content-inner">
            <div className="playlist-details-row">
              <div className="playlist-info">
                <div className={`playlist-title ${skeleton ? 'bp6-skeleton' : ''}`}>
                  {skeleton ? '' : p.title}
                </div>
                <div className={`playlist-subtitle ${skeleton ? 'bp6-skeleton' : ''}`}>
                  {skeleton ? '' : `${p.songs?.length ?? 0} songs • ${formatGenres(p.genres)}`}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlaylistCard;
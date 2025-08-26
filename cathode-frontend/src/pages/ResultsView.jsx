import React, { useState, useEffect } from 'react';
import { Button, EditableText, Alert } from '@blueprintjs/core';
import { Share, Edit } from '@blueprintjs/icons';
import SongCard from '../components/SongCard';
import ResultsHeader from '../components/ResultsHeader';
import BottomBar from '../components/BottomBar';
import './styles/results.css';

function ResultsView({ playlist, onBack, onTitleChange, onHome, onAbout }) {
  const [playlistTitle, setPlaylistTitle] = useState('');
  const [isAlertOpen, setIsAlertOpen] = useState(false);

  useEffect(() => {
    if (playlist && playlist.title) {
      const words = playlist.title.split(' ');
      const defaultTitle = words.length > 3 
        ? words.slice(0, 3).join(' ') + '...' 
        : playlist.title;
      setPlaylistTitle(defaultTitle);
    }
  }, [playlist]);

  if (!playlist) return null;

  const handleTitleChange = (newTitle) => {
    setPlaylistTitle(newTitle);
    if (onTitleChange) {
      onTitleChange(newTitle);
    }
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Export playlist:', playlist);
  };

  const handleSpotifyOpen = () => {
    // TODO: Implement Spotify integration
    console.log('Open in Spotify:', playlist);
  };

  const handleHomeClick = () => {
    setIsAlertOpen(true);
  };

  const handleAlertClose = (confirmed) => {
    setIsAlertOpen(false);
    if (confirmed) {
      onBack();
    }
  };

  return (
    <div className="results-container">
      <ResultsHeader 
        playlist={playlist}
        onBack={handleHomeClick}
        onExport={handleExport}
      />
      
      <div className="playlist-title-container">
        <Edit className="playlist-title-edit-icon" size={25} style={{ color: '#646464' }} />
        <EditableText
          value={playlistTitle}
          onChange={handleTitleChange}
          placeholder="Playlist Title"
          className="playlist-title-editable"
          maxLength={200}
          multiline={true}
        />
      </div>
      
      <div className="results-content">
        {playlist.songs.map((s) => (
          <SongCard key={s.id} s={s} />
        ))}
      </div>

      <div className="results-bottom-bar">
        <div className="results-bottom-bar-info">
          <h3>{playlistTitle}</h3>
          <p>{playlist.songs.length} songs • Perfect for your experience</p>
        </div>
        <Button 
          onClick={handleSpotifyOpen}
          text="Open in Spotify" 
          icon={<Share />}
          className="results-spotify-button"
        />
      </div>

      <BottomBar onHome={onHome} onAbout={onAbout} />

      {isAlertOpen && (
        <Alert
          isOpen={true}
          onClose={handleAlertClose}
          cancelButtonText="Cancel"
          canEscapeKeyCancel={true}
          canOutsideClickCancel={true}
          confirmButtonText="Home"
          intent="warning"
          icon="warning-sign"
        >
          <p>
            {"If you close this tab, your playlist(s) will be not saved. Export to Spotify now (or on the home page) if you want to save them."}
          </p>
        </Alert>
      )}
    </div>
  );
}

export default ResultsView;
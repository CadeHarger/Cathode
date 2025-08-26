import React from 'react';
import NewButton from '../components/NewButton';
import PlaylistCard from '../components/PlaylistCard';
import Logo from '../components/Logo';
import CustomBr from '../components/CustomBr';
import BottomBar from '../components/BottomBar';

import './styles/home.css';

function Home({ playlists, onNew, onOpenPlaylist, onHome, onAbout }) {
  return (
    <div className="container">
      <Logo text/>
      <NewButton onClick={onNew} />
      <div className="playlists-container">
        <h3 className="bp6-heading text-text-dark font-semibold mb-2">My Playlists</h3>
        <CustomBr />
        {playlists.length === 0 && <div className="bp6-text-muted">No playlists yet — create one to get started.</div>}
        {playlists.map((p) => (
          <PlaylistCard key={p.id} p={p} onOpen={onOpenPlaylist} />
        ))}
      </div>
      <BottomBar onHome={onHome} onAbout={onAbout} />
    </div>
  );
}

export default Home;
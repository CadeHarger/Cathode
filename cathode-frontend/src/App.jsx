// Cathode - React frontend (Vite + Tailwind)
// Organized with components and pages in separate files

import React, { useState } from 'react';
import Home from './pages/Home';
import NewPlaylistFlow from './pages/NewPlaylistFlow';
import ResultsView from './pages/ResultsView';
import About from './pages/About';

// ---------- Main App ----------
export default function App() {
  const [page, setPage] = useState('home'); // 'home', 'new', 'results', 'about'
  const [playlists, setPlaylists] = useState([]);
  const [activePlaylist, setActivePlaylist] = useState(null);

  function openNew() {
    setPage('new');
  }

  function openAbout() {
    setPage('about');
  }

  function openHome() {
    setPage('home');
  }

  function openSettings() {
    alert('Settings placeholder — add Firebase Auth or preferences here.');
  }

  function handleCancelNew() {
    setPage('home');
  }

  function handleCreated(playlist) {
    setPlaylists((p) => [playlist, ...p]);
    setActivePlaylist(playlist);
    setPage('results');
  }

  function openPlaylist(id) {
    const p = playlists.find((x) => x.id === id);
    if (p) {
      setActivePlaylist(p);
      setPage('results');
    }
  }

  function handleTitleChange(newTitle) {
    if (!activePlaylist) return;

    const updatedPlaylist = { ...activePlaylist, title: newTitle };
    setActivePlaylist(updatedPlaylist);

    const newPlaylists = playlists.map((p) => 
      p.id === activePlaylist.id ? updatedPlaylist : p
    );
    setPlaylists(newPlaylists);
  }

  return (
    <div className="min-h-screen bg-background text-text-dark">

      {page === 'home' && <Home playlists={playlists} onNew={openNew} onOpenPlaylist={openPlaylist} onAbout={openAbout} onHome={openHome} />}
      {page === 'new' && <NewPlaylistFlow onCancel={handleCancelNew} onCreated={handleCreated} onHome={openHome} onAbout={openAbout} />}
      {page === 'results' && (
        <ResultsView 
          playlist={activePlaylist} 
          onBack={() => setPage('home')} 
          onTitleChange={handleTitleChange}
          onAbout={openAbout}
          onHome={openHome}
        />
      )}
      {page === 'about' && <About onBack={openHome} />}
    </div>
  );
}

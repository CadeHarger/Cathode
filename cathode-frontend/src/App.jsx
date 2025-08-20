// Cathode - React frontend (Vite + Tailwind)
// Organized with components and pages in separate files

import React, { useState } from 'react';
import MobileHeader from './components/MobileHeader';
import Home from './pages/Home';
import NewPlaylistFlow from './pages/NewPlaylistFlow';
import ResultsView from './pages/ResultsView';

// ---------- Main App ----------
export default function App() {
  const [page, setPage] = useState('home'); // 'home', 'new', 'results'
  const [playlists, setPlaylists] = useState([]);
  const [activePlaylist, setActivePlaylist] = useState(null);

  function openNew() {
    setPage('new');
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

  return (
    <div className="min-h-screen bg-background text-text-dark">
      <MobileHeader onNew={openNew} onOpenSettings={openSettings} />

      {page === 'home' && <Home playlists={playlists} onNew={openNew} onOpenPlaylist={openPlaylist} />}
      {page === 'new' && <NewPlaylistFlow onCancel={handleCancelNew} onCreated={handleCreated} />}
      {page === 'results' && <ResultsView playlist={activePlaylist} onBack={() => setPage('home')} />}

      {/* simple footer / help */}
      <div className="fixed bottom-0 left-0 right-0 p-3 text-center text-slate-500 text-xs">Made with ❤️ — Cathode prototype</div>
    </div>
  );
}

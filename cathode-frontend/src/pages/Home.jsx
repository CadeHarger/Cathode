import React from 'react';
import NewButton from '../components/NewButton';
import PlaylistCard from '../components/PlaylistCard';

function Home({ playlists, onNew, onOpenPlaylist }) {
  return (
    <div className="pt-20 px-4 pb-40">
      <NewButton onClick={onNew} />
      <div className="mt-4">
        <h3 className="bp6-heading text-text-dark font-semibold mb-2">Generated Playlists</h3>
        {playlists.length === 0 && <div className="bp6-text-muted">No playlists yet — create one to get started.</div>}
        {playlists.map((p) => (
          <PlaylistCard key={p.id} p={p} onOpen={onOpenPlaylist} />
        ))}
      </div>
    </div>
  );
}

export default Home;
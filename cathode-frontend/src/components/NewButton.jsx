import React from 'react';

function NewButton({ onClick }) {
  return (
    <button onClick={onClick} className="w-full rounded-xl bg-yellow-400/95 py-6 flex items-center justify-center text-black font-bold text-lg shadow">
      + New Playlist
    </button>
  );
}

export default NewButton;
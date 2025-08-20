// Helper utility functions

export function formatDuration(ms) {
  const s = Math.round(ms / 1000);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

// Backend endpoints (adjust when you deploy backend)
export const API_CREATE_PLAYLIST = '/api/playlist'; // POST { prompt, filters } -> { id, title, songs: [...] }
export const API_GET_PLAYLIST = (id) => `/api/playlist/${id}`; // GET
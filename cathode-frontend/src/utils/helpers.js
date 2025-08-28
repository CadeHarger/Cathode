// Helper utility functions

export function formatDuration(ms) {
  const s = Math.round(ms / 1000);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

// Mobile detection utility
export const isMobile = () => {
  if (typeof window === 'undefined') return false;
  
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  
  // Check for mobile user agents
  return /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent) ||
         // Check for touch capability and small screen
         ('ontouchstart' in window && window.innerWidth < 768);
};

// Backend endpoints (adjust when you deploy backend)
export const API_BASE_URL = 'http://localhost:8000';
export const API_CREATE_PLAYLIST = `${API_BASE_URL}/api/playlist`; // POST { prompt, filters } -> { job_id }
export const API_GET_JOB_STATUS = (jobId) => `${API_BASE_URL}/api/job/${jobId}`; // GET job status
export const API_GET_PLAYLIST = (id) => `/api/playlist/${id}`; // GET (legacy)
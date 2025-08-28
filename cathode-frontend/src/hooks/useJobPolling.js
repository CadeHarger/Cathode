import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8000';

// Job status constants
export const JOB_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed'
};

/**
 * Custom hook for polling job status from the backend
 * @param {string} jobId - The job ID to poll
 * @param {Object} options - Polling options
 * @param {number} options.interval - Polling interval in milliseconds (default: 1000)
 * @param {number} options.timeout - Timeout in milliseconds (default: 300000 = 5 minutes)
 * @param {boolean} options.enabled - Whether polling is enabled (default: true)
 * @returns {Object} Job status data and control functions
 */
export const useJobPolling = (jobId, options = {}) => {
  const {
    interval = 3000, // Increased to 3 seconds to reduce server load
    timeout = 600000, // 10 minutes
    enabled = true
  } = options;

  const [jobStatus, setJobStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState(null);
  const [hasTimedOut, setHasTimedOut] = useState(false);

  const intervalRef = useRef(null);
  const timeoutRef = useRef(null);
  const startTimeRef = useRef(null);
  const isRequestInProgressRef = useRef(false);

  // Function to fetch job status
  const fetchJobStatus = useCallback(async () => {
    if (!jobId || isRequestInProgressRef.current) return;

    isRequestInProgressRef.current = true;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 20 second timeout per request

      const response = await fetch(`${API_BASE_URL}/api/job/${jobId}`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setJobStatus(data);
      setError(null);

      // Stop polling if job is completed or failed
      if (data.status === JOB_STATUS.COMPLETED || data.status === JOB_STATUS.FAILED) {
        stopPolling();
      }

      return data;
    } catch (err) {
      if (err.name === 'AbortError') {
        console.warn('Job status request was aborted');
      } else {
        console.error('Error fetching job status:', err);
        setError(err.message);
      }
      return null;
    } finally {
      isRequestInProgressRef.current = false;
    }
  }, [jobId]);

  // Start polling
  const startPolling = useCallback(() => {
    if (!jobId || !enabled) return;

    setIsPolling(true);
    setHasTimedOut(false);
    setError(null);
    startTimeRef.current = Date.now();

    // Initial fetch
    fetchJobStatus();

    // Set up polling interval
    intervalRef.current = setInterval(fetchJobStatus, interval);

    // Set up timeout
    timeoutRef.current = setTimeout(() => {
      setHasTimedOut(true);
      setError('Job polling timed out');
      stopPolling();
    }, timeout);
  }, [jobId, enabled, interval, timeout, fetchJobStatus]);

  // Stop polling
  const stopPolling = useCallback(() => {
    setIsPolling(false);
    isRequestInProgressRef.current = false;
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Restart polling
  const restartPolling = useCallback(() => {
    stopPolling();
    startPolling();
  }, [stopPolling, startPolling]);

  // Manual refresh
  const refresh = useCallback(async () => {
    return await fetchJobStatus();
  }, [fetchJobStatus]);

  // Auto-start polling when jobId changes
  useEffect(() => {
    if (jobId && enabled) {
      startPolling();
    } else {
      stopPolling();
    }

    // Cleanup on unmount or when jobId changes
    return () => {
      stopPolling();
    };
  }, [jobId, enabled, startPolling, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  // Calculate elapsed time
  const elapsedTime = startTimeRef.current 
    ? Math.floor((Date.now() - startTimeRef.current) / 1000)
    : 0;

  return {
    // Job data
    jobStatus,
    progress: jobStatus?.progress || 0,
    status: jobStatus?.status || JOB_STATUS.PENDING,
    message: jobStatus?.message || '',
    result: jobStatus?.result || null,
    
    // Status flags
    isPolling,
    isCompleted: jobStatus?.status === JOB_STATUS.COMPLETED,
    isFailed: jobStatus?.status === JOB_STATUS.FAILED,
    isInProgress: jobStatus?.status === JOB_STATUS.IN_PROGRESS,
    isPending: jobStatus?.status === JOB_STATUS.PENDING,
    
    // Error handling
    error,
    hasTimedOut,
    
    // Timing
    elapsedTime,
    
    // Control functions
    startPolling,
    stopPolling,
    restartPolling,
    refresh
  };
};

/**
 * Hook for creating a new playlist job
 * @returns {Object} Functions and state for creating playlist jobs
 */
export const useCreatePlaylist = () => {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState(null);

  const createPlaylist = useCallback(async (prompt, filters) => {
    setIsCreating(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/playlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          filters
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data.job_id;
    } catch (err) {
      console.error('Error creating playlist:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsCreating(false);
    }
  }, []);

  return {
    createPlaylist,
    isCreating,
    error
  };
};

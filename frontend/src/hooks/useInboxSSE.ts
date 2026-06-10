import { useState, useEffect, useCallback, useRef } from 'react';

import type { SentEmail } from '../api/client';

const INBOX_SSE_URL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/inbox/stream`
  : '/api/v1/inbox/stream';

export function useInboxSSE() {
  const [latestEmail, setLatestEmail] = useState<SentEmail | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const listenersRef = useRef<Set<(email: SentEmail) => void>>(new Set());

  const onNewEmail = useCallback((callback: (email: SentEmail) => void) => {
    listenersRef.current.add(callback);
    return () => {
      listenersRef.current.delete(callback);
    };
  }, []);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    const connect = () => {
      eventSource = new EventSource(INBOX_SSE_URL);

      eventSource.onopen = () => {
        setIsConnected(true);
      };

      eventSource.addEventListener('new_email', (event) => {
        try {
          const data: SentEmail = JSON.parse(event.data);
          setLatestEmail(data);
          // Notify all registered listeners
          listenersRef.current.forEach((cb) => cb(data));
        } catch (err) {
          console.error('Failed to parse inbox SSE event', err);
        }
      });

      eventSource.onerror = () => {
        setIsConnected(false);
        if (eventSource) {
          eventSource.close();
        }
        reconnectTimeout = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []);

  return { latestEmail, isConnected, onNewEmail };
}

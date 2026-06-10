import { useState, useEffect } from 'react';

const SSE_URL = import.meta.env.VITE_API_BASE_URL 
  ? `${import.meta.env.VITE_API_BASE_URL}/sse/queue`
  : '/api/v1/sse/queue';

export function useSSE() {
  const [queueLength, setQueueLength] = useState<number>(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    const connect = () => {
      console.log('Connecting to SSE...');
      eventSource = new EventSource(SSE_URL);

      eventSource.onopen = () => {
        console.log('SSE connection established');
        setIsConnected(true);
      };

      eventSource.addEventListener('queue_status', (event) => {
        try {
          const data = JSON.parse(event.data);
          setQueueLength(data.queue_length);
        } catch (err) {
          console.error('Failed to parse SSE event data', err);
        }
      });

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        setIsConnected(false);
        if (eventSource) {
          eventSource.close();
        }
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeout = setTimeout(() => {
          connect();
        }, 3000);
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

  return { queueLength, isConnected };
}

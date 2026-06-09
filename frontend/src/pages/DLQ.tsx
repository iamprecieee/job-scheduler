import React, { useEffect, useState } from 'react';
import { RefreshCw, RotateCcw } from 'lucide-react';
import { motion } from 'motion/react';
import { apiClient } from '../api/client';
import type { DeadLetterEntry, DLQListResponse } from '../api/client';

const DLQ: React.FC = () => {
  const [entries, setEntries] = useState<DeadLetterEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [replaying, setReplaying] = useState<string | null>(null);

  const fetchDLQ = async () => {
    try {
      const response = await apiClient.get<DLQListResponse>('/dlq?limit=100');
      setEntries(response.entries || []);
    } catch (error) {
      console.error('Failed to fetch DLQ entries', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDLQ();
    const interval = setInterval(fetchDLQ, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchDLQ();
  };

  const handleReplay = async (id: string) => {
    setReplaying(id);
    try {
      await apiClient.post(`/dlq/${id}/replay`);
      // Re-fetch to reflect the change immediately
      fetchDLQ();
    } catch (error) {
      console.error('Failed to replay job', error);
      alert('Failed to replay job. Check console for details.');
    } finally {
      setReplaying(null);
    }
  };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString();
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Dead Letter Queue</h1>
          <p>Manage jobs that failed after maximum retry attempts.</p>
        </div>
        
        <button 
          onClick={handleRefresh} 
          className="btn btn-secondary"
          disabled={refreshing}
        >
          <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="table-container"
      >
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading DLQ...
          </div>
        ) : entries.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No failed jobs in the DLQ.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Failure Reason</th>
                <th>Entered At</th>
                <th>Last Replay</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {entry.job_id.substring(0, 8)}...
                  </td>
                  <td style={{ 
                    maxWidth: '400px', 
                    overflow: 'hidden', 
                    textOverflow: 'ellipsis', 
                    whiteSpace: 'nowrap',
                    color: 'var(--status-failed)'
                  }} title={entry.failure_reason}>
                    {entry.failure_reason}
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{formatDate(entry.entered_at)}</td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{formatDate(entry.retry_attempted_at)}</td>
                  <td>
                    <button
                      onClick={() => handleReplay(entry.id)}
                      disabled={replaying === entry.id}
                      className="btn btn-primary"
                      style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                    >
                      <RotateCcw size={14} />
                      {replaying === entry.id ? 'Replaying...' : 'Replay'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </motion.div>
      
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
};

export default DLQ;

import React, { useEffect, useState } from 'react';
import { RefreshCw, Trash2 } from 'lucide-react';
import { motion } from 'motion/react';
import { apiClient } from '../api/client';
import type { Job, JobListResponse } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';

const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [canceling, setCanceling] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      const response = await apiClient.get<JobListResponse>('/jobs?limit=100');
      setJobs(response.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchJobs();
  };

  const handleCancel = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to cancel this job?')) return;
    
    setCanceling(jobId);
    try {
      await apiClient.post(`/jobs/${jobId}/cancel`);
      fetchJobs();
    } catch (error) {
      console.error('Failed to cancel job', error);
      alert('Failed to cancel job');
    } finally {
      setCanceling(null);
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
          <h1>Jobs</h1>
          <p>View and manage all background jobs.</p>
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
            Loading jobs...
          </div>
        ) : jobs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No jobs found.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Retries</th>
                <th>Scheduled For</th>
                <th>Interval</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {job.id.substring(0, 8)}...
                  </td>
                  <td style={{ fontWeight: 500 }}>{job.type}</td>
                  <td><PriorityBadge priority={job.priority} /></td>
                  <td><StatusBadge status={job.status} /></td>
                  <td style={{ fontSize: '0.85rem' }}>{job.retry_count}</td>
                  <td style={{ fontSize: '0.85rem' }}>{formatDate(job.scheduled_at)}</td>
                  <td style={{ fontSize: '0.85rem' }}>{job.recurring_interval ? job.recurring_interval.replace(/_/g, ' ') : '-'}</td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{formatDate(job.created_at)}</td>
                  <td>
                    {job.status === 'pending' || job.status === 'processing' ? (
                      <button
                        onClick={() => handleCancel(job.id)}
                        disabled={canceling === job.id}
                        className="btn btn-danger"
                        style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)' }}
                        title="Cancel Job"
                      >
                        <Trash2 size={16} />
                      </button>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </motion.div>
      
      {/* Spin animation for refresh button */}
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
};

export default Jobs;

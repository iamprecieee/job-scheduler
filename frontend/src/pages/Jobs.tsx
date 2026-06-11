import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { RefreshCw, Trash2, Eye, X, Filter, PlusCircle } from 'lucide-react';
import { motion } from 'motion/react';
import { apiClient } from '../api/client';
import type { Job, JobListResponse } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';

const Jobs: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [canceling, setCanceling] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [total, setTotal] = useState(0);

  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status');
  const pageParam = searchParams.get('page');
  const page = pageParam ? parseInt(pageParam, 10) : 1;
  const limit = 10;

  const fetchJobs = async () => {
    try {
      const skip = (page - 1) * limit;
      let url = `/jobs?limit=${limit}&skip=${skip}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      
      const response = await apiClient.get<JobListResponse>(url);
      setJobs(response.jobs || []);
      setTotal(response.total || 0);
    } catch (error) {
      console.error('Failed to fetch jobs', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchJobs();
    const interval = setInterval(fetchJobs, 1500); // Poll every 1.5s for near-realtime updates
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter]);

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
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {statusFilter && (
            <div className="badge badge-pending" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-text)', borderColor: 'var(--border)' }}>
              <Filter size={14} />
              Status: {statusFilter}
              <button 
                onClick={() => {
                  setSearchParams(prev => {
                    prev.delete('status');
                    prev.set('page', '1');
                    return prev;
                  });
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text)', padding: 0, display: 'flex' }}
              >
                <X size={14} />
              </button>
            </div>
          )}
          <button 
            onClick={handleRefresh} 
            className="btn btn-secondary"
            disabled={refreshing}
          >
            <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            Refresh
          </button>
          <button 
            onClick={() => navigate('/jobs/new')} 
            className="btn btn-primary"
          >
            <PlusCircle size={16} />
            Generate Job
          </button>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="table-container"
      >
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text)' }}>
            Loading jobs...
          </div>
        ) : jobs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text)' }}>
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
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--color-text)' }}>
                    {job.id.substring(0, 8)}...
                  </td>
                  <td style={{ fontWeight: 500 }}>{job.type}</td>
                  <td><PriorityBadge priority={job.priority} /></td>
                  <td><StatusBadge status={job.status} /></td>
                  <td style={{ fontSize: '0.85rem' }}>{job.retry_count}</td>
                  <td style={{ fontSize: '0.85rem' }}>{formatDate(job.scheduled_at)}</td>
                  <td style={{ fontSize: '0.85rem' }}>{job.recurring_interval ? job.recurring_interval.replace(/_/g, ' ') : '-'}</td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--color-text)' }}>{formatDate(job.created_at)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => setSelectedJob(job)}
                        className="btn btn-secondary"
                        style={{ padding: '0.4rem', borderRadius: 'var(--border-radius)' }}
                        title="View Details"
                      >
                        <Eye size={16} />
                      </button>
                      {job.status === 'pending' || job.status === 'processing' ? (
                        <button
                          onClick={() => handleCancel(job.id)}
                          disabled={canceling === job.id}
                          className="btn btn-danger"
                          style={{ padding: '0.4rem', borderRadius: 'var(--border-radius)' }}
                          title="Cancel Job"
                        >
                          <Trash2 size={16} />
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        
        {total > 0 && (
          <div style={{ 
            padding: '1rem', 
            borderTop: 'var(--border-width) solid var(--border)',
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            backgroundColor: 'var(--bg-tertiary)'
          }}>
            <span style={{ fontWeight: 'bold' }}>
              Page {page} of {Math.ceil(total / limit) || 1} <span style={{ color: 'var(--text-muted)', fontWeight: 'normal' }}>(Total: {total} jobs)</span>
            </span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                className="btn btn-secondary" 
                disabled={page <= 1} 
                onClick={() => setSearchParams(prev => { prev.set('page', String(page - 1)); return prev; })}
                style={{ padding: '0.4rem 0.8rem' }}
              >
                Previous
              </button>
              <button 
                className="btn btn-secondary" 
                disabled={page >= Math.ceil(total / limit)} 
                onClick={() => setSearchParams(prev => { prev.set('page', String(page + 1)); return prev; })}
                style={{ padding: '0.4rem 0.8rem' }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {selectedJob && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '2rem'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '800px',
            maxHeight: '90vh',
            overflowY: 'auto',
            backgroundColor: 'var(--color-background)',
            padding: '2rem',
            position: 'relative'
          }}>
            <button 
              onClick={() => setSelectedJob(null)}
              className="btn btn-secondary"
              style={{ position: 'absolute', top: '1rem', right: '1rem', padding: '0.5rem' }}
            >
              <X size={20} />
            </button>
            
            <h2>Job Details</h2>
            <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>{selectedJob.id}</span>
              <StatusBadge status={selectedJob.status} />
              <span style={{ fontWeight: 'bold', color: 'var(--color-primary)' }}>{selectedJob.type}</span>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Payload</h3>
              <pre style={{
                backgroundColor: 'var(--bg-tertiary)',
                padding: '1rem',
                border: 'var(--border-width) solid var(--border)',
                borderRadius: 'var(--border-radius)',
                boxShadow: 'inset 2px 2px 0px rgba(0,0,0,0.05)',
                overflowX: 'auto',
                fontSize: '0.85rem'
              }}>
                {JSON.stringify(selectedJob.payload, null, 2)}
              </pre>
            </div>

            {selectedJob.result && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--status-completed)' }}>Execution Result</h3>
                <pre style={{
                  backgroundColor: 'var(--bg-tertiary)',
                  padding: '1rem',
                  border: 'var(--border-width) solid var(--status-completed)',
                  borderRadius: 'var(--border-radius)',
                  boxShadow: 'inset 2px 2px 0px rgba(0,0,0,0.05)',
                  overflowX: 'auto',
                  fontSize: '0.85rem'
                }}>
                  {JSON.stringify(selectedJob.result, null, 2)}
                </pre>
              </div>
            )}

            {selectedJob.error_message && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--status-failed)' }}>Error Message</h3>
                <pre style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  padding: '1rem',
                  border: 'var(--border-width) solid var(--status-failed)',
                  borderRadius: 'var(--border-radius)',
                  boxShadow: 'inset 2px 2px 0px rgba(0,0,0,0.05)',
                  overflowX: 'auto',
                  fontSize: '0.85rem',
                  color: 'var(--status-failed)'
                }}>
                  {selectedJob.error_message}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Spin animation for refresh button */}
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
};

export default Jobs;

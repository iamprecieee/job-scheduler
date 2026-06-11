import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Clock, CheckCircle, XCircle } from 'lucide-react';
import { motion } from 'motion/react';
import { apiClient } from '../api/client';
import type { JobListResponse } from '../api/client';
import { useSSE } from '../hooks/useSSE';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { queueLength, isConnected } = useSSE();
  const [stats, setStats] = useState({
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
    cancelled: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiClient.get<JobListResponse>('/jobs?limit=1000');
        const jobs = response.jobs || [];
        
        const counts = {
          pending: jobs.filter(j => j.status === 'pending').length,
          processing: jobs.filter(j => j.status === 'processing').length,
          completed: jobs.filter(j => j.status === 'completed').length,
          failed: jobs.filter(j => j.status === 'failed').length,
          cancelled: jobs.filter(j => j.status === 'cancelled').length,
        };
        
        setStats(counts);
      } catch (error) {
        console.error('Failed to fetch jobs for stats', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    
    // Poll for stats every 1.5 seconds since we don't have SSE for all statuses yet
    const interval = setInterval(fetchStats, 1500);
    return () => clearInterval(interval);
  }, []);

  const statCards = [
    { label: 'Pending Jobs', value: stats.pending, icon: <Clock size={24} />, color: 'var(--status-pending)', link: '/jobs?status=pending' },
    { label: 'Processing', value: stats.processing, icon: <Activity size={24} />, color: 'var(--status-processing)', link: '/jobs?status=processing' },
    { label: 'Completed', value: stats.completed, icon: <CheckCircle size={24} />, color: 'var(--status-completed)', link: '/jobs?status=completed' },
    { label: 'Failed', value: stats.failed, icon: <XCircle size={24} />, color: 'var(--status-failed)', link: '/jobs?status=failed' },
    { label: 'Cancelled', value: stats.cancelled, icon: <XCircle size={24} />, color: 'var(--color-text)', link: '/jobs?status=cancelled' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Dashboard</h1>
          <p>Real-time overview of the job scheduler.</p>
        </div>
        
        <div className="glass-panel" style={{ padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              backgroundColor: isConnected ? 'var(--status-completed)' : 'var(--status-failed)',
              boxShadow: isConnected ? '0 0 10px var(--status-completed)' : 'none'
            }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text)' }}>
              {isConnected ? 'SSE Connected' : 'Disconnected'}
            </span>
          </div>
          <div style={{ width: 1, height: 24, backgroundColor: 'var(--border)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }} onClick={() => navigate('/jobs?status=pending')}>
            <Activity size={16} color="var(--color-primary)" />
            <span style={{ fontSize: '1.2rem', fontWeight: 700 }}>{queueLength}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text)' }}>in queue</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        {statCards.map((card, idx) => (
          <motion.div
            key={card.label}
            className="glass-panel"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: idx * 0.1 }}
            onClick={() => navigate(card.link)}
            style={{ padding: '1.5rem', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div style={{ color: 'var(--color-text)', fontSize: '0.9rem', fontWeight: 500 }}>
                {card.label}
              </div>
              <div style={{ color: card.color }}>
                {card.icon}
              </div>
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1 }}>
              {loading ? '-' : card.value}
            </div>
          </motion.div>
        ))}
      </div>

    </div>
  );
};

export default Dashboard;

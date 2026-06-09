import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { Save, AlertCircle } from 'lucide-react';
import { apiClient, CreateJobRequest } from '../api/client';

const CreateJob: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    type: 'send_email',
    payload: '{\n  "to": "user@example.com",\n  "subject": "Hello",\n  "body": "World"\n}',
    priority: 2,
    scheduledAt: '',
    recurringInterval: '',
    dependencies: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let parsedPayload = {};
      try {
        parsedPayload = JSON.parse(formData.payload);
      } catch (err) {
        throw new Error('Invalid JSON payload');
      }

      const request: CreateJobRequest = {
        type: formData.type,
        payload: parsedPayload,
        priority: Number(formData.priority),
      };

      if (formData.scheduledAt) {
        request.scheduled_at = new Date(formData.scheduledAt).toISOString();
      }

      if (formData.recurringInterval) {
        request.recurring_interval = formData.recurringInterval;
      }

      if (formData.dependencies.trim()) {
        request.dependencies = formData.dependencies.split(',').map(id => id.trim()).filter(id => id);
      }

      await apiClient.post('/jobs', request);
      navigate('/jobs');
    } catch (err: any) {
      setError(err.message || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Create Job</h1>
        <p>Schedule a new background task.</p>
      </div>

      <motion.div
        className="glass-panel"
        style={{ padding: '2rem' }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {error && (
          <div style={{ 
            backgroundColor: 'rgba(239, 68, 68, 0.1)', 
            border: '1px solid rgba(239, 68, 68, 0.2)', 
            padding: '1rem', 
            borderRadius: 'var(--radius-sm)',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            color: 'var(--status-failed)'
          }}>
            <AlertCircle size={20} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Job Type</label>
            <input 
              type="text" 
              name="type" 
              className="form-control" 
              value={formData.type}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Payload (JSON)</label>
            <textarea 
              name="payload" 
              className="form-control" 
              value={formData.payload}
              onChange={handleChange}
              rows={5}
              required
              style={{ fontFamily: 'monospace', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div className="form-group">
              <label className="form-label">Priority</label>
              <select 
                name="priority" 
                className="form-control" 
                value={formData.priority}
                onChange={handleChange}
              >
                <option value={1}>1 - High</option>
                <option value={2}>2 - Medium</option>
                <option value={3}>3 - Low</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Recurring Interval (Optional)</label>
              <select 
                name="recurringInterval" 
                className="form-control" 
                value={formData.recurringInterval}
                onChange={handleChange}
              >
                <option value="">None (Run Once)</option>
                <option value="every_1_minute">Every 1 Minute</option>
                <option value="every_5_minutes">Every 5 Minutes</option>
                <option value="every_1_hour">Every 1 Hour</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Scheduled At (Optional)</label>
            <input 
              type="datetime-local" 
              name="scheduledAt" 
              className="form-control" 
              value={formData.scheduledAt}
              onChange={handleChange}
            />
            <small style={{ color: 'var(--text-muted)', display: 'block', marginTop: '0.25rem' }}>
              Leave blank to run immediately.
            </small>
          </div>

          <div className="form-group">
            <label className="form-label">Dependencies (Optional)</label>
            <input 
              type="text" 
              name="dependencies" 
              className="form-control" 
              value={formData.dependencies}
              onChange={handleChange}
              placeholder="UUID1, UUID2"
            />
            <small style={{ color: 'var(--text-muted)', display: 'block', marginTop: '0.25rem' }}>
              Comma-separated Job IDs that must complete before this job runs.
            </small>
          </div>

          <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => navigate('/jobs')}
              disabled={loading}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={loading}
            >
              <Save size={18} />
              {loading ? 'Creating...' : 'Create Job'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

export default CreateJob;

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Network, PlusCircle, AlertCircle, Eye, X } from 'lucide-react';
import { motion } from 'motion/react';
import { apiClient } from '../api/client';
import type { WorkflowResponse } from '../api/client';

const Workflows: React.FC = () => {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<WorkflowResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowResponse | null>(null);

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const response = await apiClient.get<WorkflowResponse[]>('/workflows');
        setWorkflows(response);
      } catch (err) {
        console.error('Failed to fetch workflows', err);
        setError('Failed to load workflows. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflows();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Workflows</h1>
          <p>Manage your scheduled DAG workflows and recurring templates.</p>
        </div>
        <button 
          className="btn btn-primary" 
          onClick={() => navigate('/workflows/new')}
        >
          <PlusCircle size={18} />
          Create Workflow
        </button>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: 'rgba(239, 68, 68, 0.1)', 
          border: '1px solid rgba(239, 68, 68, 0.2)', 
          padding: '1rem', 
          borderRadius: 'var(--border-radius)',
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

      {loading ? (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading workflows...
        </div>
      ) : workflows.length === 0 ? (
        <div className="glass-panel" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
          <Network size={48} color="var(--text-muted)" style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
          <h2 style={{ marginBottom: '0.5rem' }}>No Workflows Found</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', maxWidth: 400, margin: '0 auto 1.5rem' }}>
            Workflows allow you to run multiple jobs in a sequence (DAG) and on a recurring schedule.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/workflows/new')}>
            Create Your First Workflow
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
          {workflows.map((workflow, idx) => (
            <motion.div
              key={workflow.id}
              className="glass-panel"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.05 }}
              style={{ padding: '1.5rem' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Network size={18} color="var(--color-primary)" />
                    {workflow.name || 'Unnamed Workflow'}
                  </h3>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem', fontFamily: 'monospace' }}>
                    ID: {workflow.id}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <button
                    onClick={() => setSelectedWorkflow(workflow)}
                    className="btn btn-secondary"
                    style={{ padding: '0.4rem', borderRadius: 'var(--border-radius)', marginRight: '0.5rem' }}
                    title="View Details"
                  >
                    <Eye size={16} />
                  </button>
                  {workflow.recurring_interval && (
                    <span style={{ 
                      backgroundColor: 'rgba(59, 130, 246, 0.1)', 
                      color: '#3b82f6', 
                      padding: '0.25rem 0.5rem', 
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      textTransform: 'uppercase'
                    }}>
                      Recurring: {workflow.recurring_interval}
                    </span>
                  )}
                  {workflow.scheduled_at && (
                    <span style={{ 
                      backgroundColor: 'rgba(168, 85, 247, 0.1)', 
                      color: '#a855f7', 
                      padding: '0.25rem 0.5rem', 
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      textTransform: 'uppercase'
                    }}>
                      Next Run: {new Date(workflow.scheduled_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Steps</div>
                  <div style={{ fontWeight: 'bold', fontSize: '1.25rem' }}>{workflow.nodes.length}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Created</div>
                  <div style={{ fontWeight: 'bold', fontSize: '1rem', marginTop: '0.25rem' }}>{new Date(workflow.created_at).toLocaleDateString()}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {selectedWorkflow && (
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
              onClick={() => setSelectedWorkflow(null)}
              className="btn btn-secondary"
              style={{ position: 'absolute', top: '1rem', right: '1rem', padding: '0.5rem' }}
            >
              <X size={20} />
            </button>
            
            <h2>Workflow Details</h2>
            <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>{selectedWorkflow.id}</span>
              {selectedWorkflow.name && <span style={{ fontWeight: 'bold', color: 'var(--color-primary)' }}>{selectedWorkflow.name}</span>}
            </div>

            <div style={{ marginBottom: '1.5rem', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
              <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '1rem', borderRadius: 'var(--border-radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Created At</div>
                <div style={{ fontWeight: 'bold', marginTop: '0.25rem' }}>{new Date(selectedWorkflow.created_at).toLocaleString()}</div>
              </div>
              <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '1rem', borderRadius: 'var(--border-radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Next Run</div>
                <div style={{ fontWeight: 'bold', marginTop: '0.25rem' }}>{selectedWorkflow.scheduled_at ? new Date(selectedWorkflow.scheduled_at).toLocaleString() : 'Immediate'}</div>
              </div>
              <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '1rem', borderRadius: 'var(--border-radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Recurring</div>
                <div style={{ fontWeight: 'bold', marginTop: '0.25rem' }}>{selectedWorkflow.recurring_interval || 'None'}</div>
              </div>
            </div>

            <div>
              <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Steps ({selectedWorkflow.nodes.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {selectedWorkflow.nodes.map(node => (
                  <div key={node.id} style={{ 
                    padding: '1rem', 
                    border: '1px solid var(--border)', 
                    borderRadius: 'var(--border-radius)',
                    backgroundColor: 'var(--bg-tertiary)' 
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 'bold', color: 'var(--color-primary)' }}>{node.client_id}</span>
                      <span className="badge badge-pending" style={{ color: 'var(--color-text)', borderColor: 'var(--border)' }}>
                        {node.type}
                      </span>
                    </div>
                    {node.dependencies.length > 0 && (
                      <div style={{ fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
                        Depends on: {node.dependencies.join(', ')}
                      </div>
                    )}
                    <pre style={{
                      backgroundColor: 'var(--color-background)',
                      padding: '0.75rem',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      fontSize: '0.8rem',
                      margin: 0,
                      overflowX: 'auto'
                    }}>
                      {JSON.stringify(node.payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workflows;

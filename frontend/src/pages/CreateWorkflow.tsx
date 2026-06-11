import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { CreateWorkflowRequest, WorkflowNodeRequest } from '../api/client';
import { Save, AlertCircle, Plus, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import Select from '../components/Select';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";

const JOB_TYPES = [
  { value: 'send_email', label: 'Send Email' },
  { value: 'generate_report', label: 'Generate Report' },
  { value: 'upload_file', label: 'Upload File' },
];

const DEFAULT_PAYLOADS: Record<string, Record<string, unknown>> = {
  send_email: { to: 'user@example.com', subject: 'Hello', body: 'World' },
  generate_report: { report_type: 'daily_summary' },
  upload_file: { file_name: 'summary.pdf', destination: 's3://reports' },
};

type WorkflowNodeUI = WorkflowNodeRequest & {
  payloadString: string;
};

export default function CreateWorkflow() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [workflowName, setWorkflowName] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [recurringInterval, setRecurringInterval] = useState('');
  
  const [nodes, setNodes] = useState<WorkflowNodeUI[]>([
    {
      client_id: 'node_1',
      type: 'generate_report',
      payload: { report_type: 'daily_summary' },
      payloadString: '{\n  "report_type": "daily_summary"\n}',
      priority: 2,
      dependencies: []
    }
  ]);

  const addNode = () => {
    const nextId = `node_${nodes.length + 1}`;
    const defaultPayload = DEFAULT_PAYLOADS['upload_file'];
    
    setNodes([
      ...nodes,
      {
        client_id: nextId,
        type: 'upload_file',
        payload: defaultPayload,
        payloadString: JSON.stringify(defaultPayload, null, 2),
        priority: 2,
        dependencies: []
      }
    ]);
  };

  const updateNode = (index: number, field: keyof WorkflowNodeUI, value: any) => {
    const newNodes = [...nodes];
    newNodes[index] = { ...newNodes[index], [field]: value };
    setNodes(newNodes);
  };

  const removeNode = (index: number) => {
    const nodeToRemove = nodes[index];
    // Remove node and also remove it from any other node's dependencies
    const newNodes = nodes.filter((_, i) => i !== index).map(node => ({
      ...node,
      dependencies: node.dependencies.filter(dep => dep !== nodeToRemove.client_id)
    }));
    setNodes(newNodes);
  };

  const handlePayloadChange = (index: number, e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const str = e.target.value;
    const newNodes = [...nodes];
    newNodes[index].payloadString = str;
    
    try {
      const parsed = JSON.parse(str);
      newNodes[index].payload = parsed;
      e.target.setCustomValidity('');
    } catch {
      e.target.setCustomValidity('Invalid JSON');
    }
    
    setNodes(newNodes);
  };

  const handleDependencyChange = (index: number, depId: string, checked: boolean) => {
    const currentDeps = nodes[index].dependencies;
    let newDeps = [...currentDeps];
    if (checked) {
      newDeps.push(depId);
    } else {
      newDeps = newDeps.filter(id => id !== depId);
    }
    updateNode(index, 'dependencies', newDeps);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (nodes.length === 0) {
      setError('A workflow must have at least one node.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const request: CreateWorkflowRequest = {
        name: workflowName || undefined,
        nodes: nodes.map(({ payloadString, ...rest }) => rest),
      };

      if (scheduledAt) {
        request.scheduled_at = new Date(scheduledAt).toISOString();
      }
      if (recurringInterval) {
        request.recurring_interval = recurringInterval;
      }

      await apiClient.post('/workflows', request);
      navigate('/jobs'); // Or to a workflows list page if one exists
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to create workflow');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Create DAG Workflow</h1>
        <p>Design a directed acyclic graph of jobs that execute in sequence.</p>
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
          
          <div style={{ marginBottom: '2rem', paddingBottom: '2rem', borderBottom: '1px solid var(--border)' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', color: 'var(--color-text)' }}>Workflow Settings</h2>
            
            <div className="form-group">
              <label className="form-label" htmlFor="workflowName">Workflow Name (Optional)</label>
              <input
                id="workflowName"
                className="form-control"
                type="text"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                placeholder="e.g. Daily Data Pipeline"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="scheduledAt">Schedule First Run (Optional)</label>
                <div style={{ position: 'relative' }}>
                  <DatePicker
                    selected={scheduledAt ? new Date(scheduledAt) : null}
                    onChange={(date: Date | null) => setScheduledAt(date ? date.toISOString() : '')}
                    showTimeSelect
                    timeFormat="HH:mm"
                    timeIntervals={15}
                    dateFormat="MMMM d, yyyy h:mm aa"
                    placeholderText="Select Date & Time..."
                    className="form-control"
                    wrapperClassName="w-full"
                    isClearable
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="recurringInterval">Recurring Schedule (Optional)</label>
                <Select
                  options={[
                    { value: '', label: 'None (Run Once)' },
                    { value: 'every_1_minute', label: 'Every 1 Minute' },
                    { value: 'every_5_minutes', label: 'Every 5 Minutes' },
                    { value: 'every_1_hour', label: 'Every 1 Hour' },
                  ]}
                  value={recurringInterval}
                  onChange={(val) => setRecurringInterval(val)}
                />
              </div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', color: 'var(--color-text)', margin: 0 }}>Workflow Steps</h2>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <AnimatePresence>
                {nodes.map((node, index) => (
                  <motion.div 
                    key={node.client_id}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    style={{ 
                      border: '1px solid var(--border)', 
                      borderRadius: 'var(--border-radius)', 
                      padding: '1.5rem',
                      backgroundColor: 'var(--bg-tertiary)',
                      position: 'relative'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                      <h3 style={{ margin: 0, color: 'var(--color-primary)', fontSize: '1.1rem', fontFamily: 'monospace', textTransform: 'uppercase' }}>
                        Step {index + 1}: {node.client_id}
                      </h3>
                      <button 
                        type="button" 
                        onClick={() => removeNode(index)} 
                        disabled={nodes.length === 1}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: nodes.length === 1 ? 'not-allowed' : 'pointer',
                          color: nodes.length === 1 ? 'var(--text-muted)' : 'var(--status-failed)'
                        }}
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                      <div className="form-group">
                        <label className="form-label">Job Type</label>
                        <Select
                          options={JOB_TYPES}
                          value={node.type}
                          onChange={(val) => {
                            const newNodes = [...nodes];
                            const defaultPayload = DEFAULT_PAYLOADS[val] || {};
                            newNodes[index].type = val;
                            newNodes[index].payload = defaultPayload;
                            newNodes[index].payloadString = JSON.stringify(defaultPayload, null, 2);
                            setNodes(newNodes);
                          }}
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label">Priority</label>
                        <Select
                          options={[
                            { value: '1', label: '1 - High' },
                            { value: '2', label: '2 - Medium' },
                            { value: '3', label: '3 - Low' },
                          ]}
                          value={String(node.priority)}
                          onChange={(val) => updateNode(index, 'priority', parseInt(val))}
                        />
                      </div>
                    </div>

                    <div className="form-group" style={{ marginTop: '1.5rem' }}>
                      <label className="form-label">Depends On</label>
                      {index === 0 ? (
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No previous steps available to depend on. This step will run immediately.</span>
                      ) : (
                        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', padding: '0.5rem 0' }}>
                          {nodes.slice(0, index).map(prevNode => (
                            <label key={prevNode.client_id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', cursor: 'pointer', color: 'var(--color-text)' }}>
                              <input 
                                type="checkbox" 
                                checked={node.dependencies.includes(prevNode.client_id)}
                                onChange={(e) => handleDependencyChange(index, prevNode.client_id, e.target.checked)}
                                style={{ accentColor: 'var(--color-primary)' }}
                              />
                              {prevNode.client_id}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="form-group" style={{ marginTop: '1.5rem' }}>
                      <label className="form-label">Payload (JSON)</label>
                      <textarea
                        className="form-control"
                        rows={4}
                        value={node.payloadString}
                        onChange={(e) => handlePayloadChange(index, e)}
                        placeholder='{"key": "value"}'
                        required
                        style={{ fontFamily: 'monospace', resize: 'vertical' }}
                      />
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
            
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={addNode} 
              style={{ padding: '0.75rem 1rem', marginTop: '1.5rem', width: '100%', justifyContent: 'center', borderStyle: 'dashed' }}
            >
              <Plus size={16} /> Add Step
            </button>
          </div>

          <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => navigate('/jobs')}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              <Save size={18} />
              {isSubmitting ? 'Creating Workflow...' : 'Create Workflow'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

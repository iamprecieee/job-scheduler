import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Mail, X, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { apiClient } from '../api/client';
import type { SentEmail, SentEmailListResponse } from '../api/client';
import { useInboxSSE } from '../hooks/useInboxSSE';

const Inbox: React.FC = () => {
  const [emails, setEmails] = useState<SentEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<SentEmail | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [newCount, setNewCount] = useState(0);
  const limit = 15;

  const { isConnected, onNewEmail } = useInboxSSE();

  const fetchEmails = useCallback(async () => {
    try {
      const skip = (page - 1) * limit;
      const response = await apiClient.get<SentEmailListResponse>(
        `/inbox?limit=${limit}&skip=${skip}`
      );
      setEmails(response.emails || []);
      setTotal(response.total || 0);
    } catch (error) {
      console.error('Failed to fetch emails', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [page]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchEmails();
  }, [fetchEmails]);

  // SSE: when a new email arrives, prepend it to the list in real-time
  useEffect(() => {
    const unsubscribe = onNewEmail((email: SentEmail) => {
      setEmails((prev) => {
        // Avoid duplicates
        if (prev.some((e) => e.id === email.id)) return prev;
        const updated = [email, ...prev];
        // Keep list within page limit
        return updated.slice(0, limit);
      });
      setTotal((prev) => prev + 1);
      setNewCount((prev) => prev + 1);

      // Clear the "new" indicator after 3 seconds
      setTimeout(() => setNewCount((prev) => Math.max(0, prev - 1)), 3000);
    });

    return unsubscribe;
  }, [onNewEmail]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchEmails();
  };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const formatFullDate = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h1>Inbox</h1>
            {newCount > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                style={{
                  backgroundColor: 'var(--status-completed)',
                  color: '#fff',
                  borderRadius: '999px',
                  padding: '0.15rem 0.6rem',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                }}
              >
                {newCount} new
              </motion.div>
            )}
          </div>
          <p>Emails sent by completed jobs appear here in real-time.</p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="glass-panel" style={{
            padding: '0.5rem 1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.8rem',
          }}>
            <div style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: isConnected ? 'var(--status-completed)' : 'var(--status-failed)',
              boxShadow: isConnected ? '0 0 10px var(--status-completed)' : 'none',
            }} />
            {isConnected ? 'Live' : 'Offline'}
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
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="table-container"
      >
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text)' }}>
            Loading inbox...
          </div>
        ) : emails.length === 0 ? (
          <div style={{
            padding: '4rem',
            textAlign: 'center',
            color: 'var(--text-muted)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem',
          }}>
            <Mail size={48} strokeWidth={1} />
            <div>
              <p style={{ fontWeight: 600, fontSize: '1.1rem', marginBottom: '0.25rem' }}>No emails yet</p>
              <p style={{ fontSize: '0.85rem' }}>Create a <code>send_email</code> job and it will appear here once processed.</p>
            </div>
          </div>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th style={{ width: '40px' }}></th>
                  <th>Recipient</th>
                  <th>Subject</th>
                  <th>Sent</th>
                  <th style={{ width: '40px' }}></th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {emails.map((email) => (
                    <motion.tr
                      key={email.id}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.25 }}
                      onClick={() => setSelectedEmail(email)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>
                        <div style={{
                          width: 28,
                          height: 28,
                          borderRadius: 'var(--border-radius)',
                          background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary, var(--color-primary)))',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: '2px solid var(--border)',
                        }}>
                          <Mail size={14} color="white" />
                        </div>
                      </td>
                      <td style={{ fontWeight: 600 }}>{email.recipient}</td>
                      <td style={{ color: 'var(--color-text)' }}>{email.subject}</td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                        {formatDate(email.sent_at)}
                      </td>
                      <td>
                        <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>

            {total > limit && (
              <div style={{
                padding: '1rem',
                borderTop: 'var(--border-width) solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: 'var(--bg-tertiary)',
              }}>
                <span style={{ fontWeight: 'bold' }}>
                  Page {page} of {Math.ceil(total / limit) || 1}{' '}
                  <span style={{ color: 'var(--text-muted)', fontWeight: 'normal' }}>
                    ({total} emails)
                  </span>
                </span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-secondary"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                    style={{ padding: '0.4rem 0.8rem' }}
                  >
                    Previous
                  </button>
                  <button
                    className="btn btn-secondary"
                    disabled={page >= Math.ceil(total / limit)}
                    onClick={() => setPage((p) => p + 1)}
                    style={{ padding: '0.4rem 0.8rem' }}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </motion.div>

      {/* Email Detail Modal */}
      {selectedEmail && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '2rem',
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedEmail(null);
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="glass-panel"
            style={{
              width: '100%',
              maxWidth: '700px',
              maxHeight: '85vh',
              overflowY: 'auto',
              backgroundColor: 'var(--color-background)',
              padding: '2rem',
              position: 'relative',
            }}
          >
            <button
              onClick={() => setSelectedEmail(null)}
              className="btn btn-secondary"
              style={{ position: 'absolute', top: '1rem', right: '1rem', padding: '0.5rem' }}
            >
              <X size={20} />
            </button>

            {/* Email Header */}
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: 'var(--border-radius)',
                  background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary, var(--color-primary)))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid var(--border)',
                  boxShadow: '2px 2px 0px var(--border)',
                }}>
                  <Mail size={18} color="white" />
                </div>
                <h2 style={{ margin: 0 }}>{selectedEmail.subject}</h2>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr',
                gap: '0.5rem 1rem',
                fontSize: '0.85rem',
                padding: '1rem',
                backgroundColor: 'var(--bg-tertiary)',
                border: 'var(--border-width) solid var(--border)',
                borderRadius: 'var(--border-radius)',
              }}>
                <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>To:</span>
                <span style={{ fontWeight: 600 }}>{selectedEmail.recipient}</span>

                <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>Sent:</span>
                <span>{formatFullDate(selectedEmail.sent_at)}</span>

                <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>Job ID:</span>
                <span style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{selectedEmail.job_id}</span>
              </div>
            </div>

            {/* Email Body */}
            <div>
              <h3 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Message Body
              </h3>
              <div style={{
                backgroundColor: 'var(--bg-tertiary)',
                padding: '1.5rem',
                border: 'var(--border-width) solid var(--border)',
                borderRadius: 'var(--border-radius)',
                boxShadow: 'inset 2px 2px 0px rgba(0,0,0,0.05)',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                fontFamily: 'inherit',
              }}>
                {selectedEmail.body}
              </div>
            </div>
          </motion.div>
        </div>
      )}

      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
};

export default Inbox;

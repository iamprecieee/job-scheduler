import React, { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, ListTodo, PlusCircle, AlertOctagon, Mail, Sun, Moon, Clock, X, Network } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useInboxSSE } from '../hooks/useInboxSSE';
import type { SentEmail } from '../api/client';

const Layout: React.FC = () => {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

  const [globalUnreadCount, setGlobalUnreadCount] = useState(0);
  const [toastEmail, setToastEmail] = useState<SentEmail | null>(null);
  const { onNewEmail } = useInboxSSE();

  useEffect(() => {
    const unsubscribe = onNewEmail((email) => {
      // Don't show global notification if they are already looking at the inbox
      if (window.location.pathname !== '/inbox') {
        setGlobalUnreadCount((prev) => prev + 1);
        setToastEmail(email);
        setTimeout(() => setToastEmail(null), 5000);
      }
    });
    return unsubscribe;
  }, [onNewEmail]);

  // Clear unread count when navigating to inbox
  useEffect(() => {
    if (window.location.pathname === '/inbox') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setGlobalUnreadCount(0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [window.location.pathname]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };
  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/jobs', icon: <ListTodo size={20} />, label: 'Jobs' },
    { to: '/workflows', icon: <Network size={20} />, label: 'Workflows' },
    { to: '/jobs/new', icon: <PlusCircle size={20} />, label: 'Create Job' },
    { to: '/workflows/new', icon: <PlusCircle size={20} />, label: 'Create Workflow' },
    { to: '/inbox', icon: <Mail size={20} />, label: 'Inbox' },
    { to: '/dlq', icon: <AlertOctagon size={20} />, label: 'DLQ' },
  ];

  return (
    <div className="grid-bg" style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{
          width: 'var(--sidebar-width)',
          backgroundColor: 'var(--color-background)',
          borderRight: 'var(--border-width) solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          position: 'fixed',
          top: 0,
          bottom: 0,
          left: 0,
          zIndex: 10,
        }}
      >
        <div style={{ padding: '2rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 'var(--border-radius)',
            background: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid var(--border)',
            boxShadow: '2px 2px 0px var(--border)'
          }}>
            <Clock size={20} color="white" />
          </div>
          <span style={{ fontSize: '1.2rem', fontFamily: 'monospace', fontWeight: 800, textTransform: 'uppercase', color: 'var(--color-primary)' }}>
            Scheduler
          </span>
        </div>

        <nav style={{ padding: '0 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end
              onClick={() => {
                if (item.label === 'Inbox') setGlobalUnreadCount(0);
              }}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.75rem 1rem',
                border: isActive ? 'var(--border-width) solid var(--border)' : 'var(--border-width) solid transparent',
                borderRadius: 'var(--border-radius)',
                color: 'var(--color-text)',
                backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
                boxShadow: isActive ? '4px 4px 0px var(--border)' : 'none',
                fontWeight: 'bold',
                fontFamily: 'monospace',
                textTransform: 'uppercase',
                transition: 'all 0.1s ease',
                textDecoration: 'none',
              })}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ color: 'inherit', opacity: 0.8 }}>
                  {item.icon}
                </div>
                {item.label}
              </div>
              {item.label === 'Inbox' && globalUnreadCount > 0 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  style={{
                    backgroundColor: 'var(--status-completed)',
                    color: '#fff',
                    borderRadius: '999px',
                    padding: '0.1rem 0.5rem',
                    fontSize: '0.7rem',
                  }}
                >
                  {globalUnreadCount}
                </motion.div>
              )}
            </NavLink>
          ))}
        </nav>
        
        <div style={{ padding: '1.5rem', borderTop: 'var(--border-width) solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 'bold' }}>
            v1.0.0-beta
          </div>
          <button 
            onClick={toggleTheme}
            style={{
              background: 'transparent',
              border: '2px solid var(--border)',
              borderRadius: '50%',
              width: '30px',
              height: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--color-text)',
              boxShadow: '2px 2px 0px var(--border)'
            }}
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
      </motion.aside>

      {/* Main Content Area */}
      <main style={{
        flex: 1,
        marginLeft: 'var(--sidebar-width)',
        padding: '2rem 3rem',
        maxWidth: '1400px',
      }}>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1, ease: 'easeOut' }}
        >
          <Outlet />
        </motion.div>
      </main>

      {/* Global Toast Notification */}
      <AnimatePresence>
        {toastEmail && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            style={{
              position: 'fixed',
              bottom: '2rem',
              right: '2rem',
              zIndex: 1000,
              backgroundColor: 'var(--color-background)',
              border: '2px solid var(--status-completed)',
              borderRadius: 'var(--border-radius)',
              boxShadow: '4px 4px 0px var(--status-completed)',
              padding: '1rem',
              maxWidth: '350px',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--status-completed)', fontWeight: 'bold', fontSize: '0.85rem', textTransform: 'uppercase' }}>
                <Mail size={16} />
                New Email Sent
              </div>
              <button onClick={() => setToastEmail(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                <X size={16} />
              </button>
            </div>
            <div style={{ fontSize: '0.9rem' }}>
              <strong>To:</strong> {toastEmail.recipient}
            </div>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              <strong>Sub:</strong> {toastEmail.subject}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Layout;

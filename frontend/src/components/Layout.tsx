import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, ListTodo, PlusCircle, AlertOctagon } from 'lucide-react';
import { motion } from 'motion/react';

const Layout: React.FC = () => {
  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/jobs', icon: <ListTodo size={20} />, label: 'Jobs' },
    { to: '/create', icon: <PlusCircle size={20} />, label: 'Create Job' },
    { to: '/dlq', icon: <AlertOctagon size={20} />, label: 'DLQ' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{
          width: 'var(--sidebar-width)',
          backgroundColor: 'var(--bg-tertiary)',
          borderRight: '1px solid var(--border)',
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
            borderRadius: 'var(--radius-sm)',
            background: 'var(--accent-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px var(--accent-glow)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            Antigravity
          </span>
        </div>

        <nav style={{ padding: '0 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                fontWeight: isActive ? 600 : 500,
                transition: 'all 0.2s ease',
                textDecoration: 'none',
              })}
            >
              <div style={{ 
                color: 'inherit',
                opacity: 0.8,
              }}>
                {item.icon}
              </div>
              {item.label}
            </NavLink>
          ))}
        </nav>
        
        <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            v1.0.0-beta
          </div>
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
    </div>
  );
};

export default Layout;

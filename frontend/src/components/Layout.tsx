import React, { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, ListTodo, PlusCircle, AlertOctagon, Sun, Moon, Clock } from 'lucide-react';
import { motion } from 'motion/react';

const Layout: React.FC = () => {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

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
    { to: '/create', icon: <PlusCircle size={20} />, label: 'Create Job' },
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
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
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
    </div>
  );
};

export default Layout;

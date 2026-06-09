import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

interface Option {
  value: string;
  label: string;
}

interface SelectProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  id?: string;
}

const Select: React.FC<SelectProps> = ({ options, value, onChange, placeholder = 'Select...', id }) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="select-container" ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      <button
        type="button"
        id={id}
        className="form-control"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          textAlign: 'left',
          backgroundColor: isOpen ? 'var(--bg-tertiary)' : 'var(--color-background)',
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>{selectedOption ? selectedOption.label : placeholder}</span>
        <ChevronDown 
          size={16} 
          style={{ 
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', 
            transition: 'transform 0.2s ease' 
          }} 
        />
      </button>

      {isOpen && (
        <div 
          className="select-dropdown glass-panel animate-fade-in"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 50,
            marginTop: '0.2rem',
            maxHeight: '250px',
            overflowY: 'auto',
            padding: '0.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.25rem'
          }}
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              className="select-option"
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: '0.5rem 0.75rem',
                border: 'var(--border-width) solid transparent',
                backgroundColor: option.value === value ? 'var(--color-primary)' : 'transparent',
                color: option.value === value ? 'var(--color-background)' : 'var(--color-text)',
                fontFamily: 'inherit',
                fontWeight: 'bold',
                cursor: 'pointer',
                borderRadius: 'var(--border-radius)',
                transition: 'all 0.1s ease',
              }}
              onMouseEnter={(e) => {
                if (option.value !== value) {
                  e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                  e.currentTarget.style.borderColor = 'var(--border)';
                }
              }}
              onMouseLeave={(e) => {
                if (option.value !== value) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.borderColor = 'transparent';
                }
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default Select;

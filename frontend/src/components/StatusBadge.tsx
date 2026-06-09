import React from 'react';
import type { JobStatus } from '../api/client';

interface StatusBadgeProps {
  status: JobStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  return (
    <span className={`badge badge-${status}`}>
      {status}
    </span>
  );
};

export default StatusBadge;

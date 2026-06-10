import React from 'react';

interface PriorityBadgeProps {
  priority: number;
}

const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
  let label: string;
  let colorClass = 'badge-cancelled'; // Neutral look

  if (priority === 1) {
    label = 'High';
    colorClass = 'badge-failed'; // Red-ish
  } else if (priority === 2) {
    label = 'Medium';
    colorClass = 'badge-pending'; // Yellow-ish
  } else if (priority === 3) {
    label = 'Low';
    colorClass = 'badge-completed'; // Green-ish
  } else {
    label = priority.toString();
  }

  return (
    <span className={`badge ${colorClass}`}>
      {label}
    </span>
  );
};

export default PriorityBadge;

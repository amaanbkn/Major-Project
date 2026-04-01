import React from 'react';

export const Skeleton = ({ className = "" }) => {
  return (
    <div className={`animate-shimmer rounded-[8px] bg-[#F7F8F5] ${className}`}></div>
  );
};

import React from 'react';

export const Card = ({ className = "", children, hoverable = false, ...props }) => {
  const baseStyles = "bg-white border border-[#E5E7EB] rounded-[16px] shadow-[0_1px_3px_rgba(0,0,0,0.06)] overflow-hidden";
  const hoverStyles = hoverable ? "transition-all duration-200 ease-in-out hover:-translate-y-[2px] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)]" : "";
  
  return (
    <div className={`${baseStyles} ${hoverStyles} ${className}`} {...props}>
      {children}
    </div>
  );
};

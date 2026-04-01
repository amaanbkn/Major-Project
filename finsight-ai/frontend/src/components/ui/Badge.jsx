import React from 'react';

export const Badge = ({ children, variant = "neutral", className = "" }) => {
  const baseStyles = "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium tracking-[0.08em] uppercase whitespace-nowrap";
  
  const variants = {
    success: "bg-[#22C55E]/10 text-[#22C55E]",
    danger: "bg-[#EF4444]/10 text-[#EF4444]",
    neutral: "bg-[#F3F4F6] text-[#6B7280]",
    dark: "bg-[#111111] text-white"
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

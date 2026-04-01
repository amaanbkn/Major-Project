import React from 'react';

export const Input = React.forwardRef(({ className = "", ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={`w-full bg-[#F7F8F5] border border-[#E5E7EB] rounded-[12px] px-4 py-[14px] text-[14px] text-[#111111] placeholder:text-[#6B7280] focus:outline-none focus:border-[#111111] transition-colors duration-200 ${className}`}
      {...props}
    />
  );
});
Input.displayName = "Input";

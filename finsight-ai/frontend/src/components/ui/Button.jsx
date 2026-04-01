import React from 'react';

export const Button = React.forwardRef(({ 
  className = "", 
  variant = "primary", 
  size = "md", 
  children, 
  ...props 
}, ref) => {
  const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-200 ease-in-out focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";
  
  const variants = {
    primary: "bg-[#111111] text-white hover:opacity-85 active:scale-95 rounded-[8px]",
    outline: "bg-transparent text-[#111111] border border-[#111111] hover:bg-[#F7F8F5] active:scale-95 rounded-[8px]",
    ghost: "bg-transparent text-[#6B7280] hover:text-[#111111] hover:bg-[#F3F4F6] active:scale-95 rounded-[8px]"
  };
  
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2.5 text-sm w-full md:w-auto",
    lg: "px-6 py-3 text-base"
  };

  return (
    <button
      ref={ref}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
});
Button.displayName = "Button";

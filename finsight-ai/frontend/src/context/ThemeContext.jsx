import React, { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('finsight-theme') || 'light';
  });

  const [preferences, setPreferences] = useState(() => {
    const saved = localStorage.getItem('finsight-preferences');
    return saved ? JSON.parse(saved) : { notifications: true, autoPlay: false };
  });

  useEffect(() => {
    localStorage.setItem('finsight-theme', theme);
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('finsight-preferences', JSON.stringify(preferences));
  }, [preferences]);

  const value = {
    theme,
    setTheme,
    preferences,
    updatePreferences: (newPrefs) => setPreferences(prev => ({ ...prev, ...newPrefs }))
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

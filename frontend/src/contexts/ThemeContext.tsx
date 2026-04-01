import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

type Theme = 'dark' | 'light' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  compactMode: boolean;
  setCompactMode: (compact: boolean) => void;
  showConfidence: boolean;
  setShowConfidence: (show: boolean) => void;
  showReasoning: boolean;
  setShowReasoning: (show: boolean) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  resolvedTheme: 'dark' | 'light';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'ng_theme';
const COMPACT_STORAGE_KEY = 'ng_compact_mode';
const CONFIDENCE_STORAGE_KEY = 'ng_show_confidence';
const REASONING_STORAGE_KEY = 'ng_show_reasoning';
const SIDEBAR_STORAGE_KEY = 'ng_sidebar_collapsed';

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return (stored as Theme) || 'dark';
  });

  const [compactMode, setCompactModeState] = useState(() => {
    const stored = localStorage.getItem(COMPACT_STORAGE_KEY);
    return stored === 'true';
  });

  const [showConfidence, setShowConfidenceState] = useState(() => {
    const stored = localStorage.getItem(CONFIDENCE_STORAGE_KEY);
    return stored !== 'false'; // Default true
  });

  const [showReasoning, setShowReasoningState] = useState(() => {
    const stored = localStorage.getItem(REASONING_STORAGE_KEY);
    return stored !== 'false'; // Default true
  });

  const [sidebarCollapsed, setSidebarCollapsedState] = useState(() => {
    const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY);
    return stored === 'true';
  });

  const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>('dark');

  // Resolve system theme
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const updateResolvedTheme = () => {
      if (theme === 'system') {
        setResolvedTheme(mediaQuery.matches ? 'dark' : 'light');
      } else {
        setResolvedTheme(theme as 'dark' | 'light');
      }
    };

    updateResolvedTheme();
    mediaQuery.addEventListener('change', updateResolvedTheme);
    return () => mediaQuery.removeEventListener('change', updateResolvedTheme);
  }, [theme]);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolvedTheme);
    
    // Apply compact mode
    if (compactMode) {
      root.classList.add('compact');
    } else {
      root.classList.remove('compact');
    }
  }, [resolvedTheme, compactMode]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
  };

  const setCompactMode = (compact: boolean) => {
    setCompactModeState(compact);
    localStorage.setItem(COMPACT_STORAGE_KEY, String(compact));
  };

  const setShowConfidence = (show: boolean) => {
    setShowConfidenceState(show);
    localStorage.setItem(CONFIDENCE_STORAGE_KEY, String(show));
  };

  const setShowReasoning = (show: boolean) => {
    setShowReasoningState(show);
    localStorage.setItem(REASONING_STORAGE_KEY, String(show));
  };

  const setSidebarCollapsed = (collapsed: boolean) => {
    setSidebarCollapsedState(collapsed);
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        compactMode,
        setCompactMode,
        showConfidence,
        setShowConfidence,
        showReasoning,
        setShowReasoning,
        sidebarCollapsed,
        setSidebarCollapsed,
        resolvedTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

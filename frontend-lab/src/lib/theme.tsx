import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ThemeId = "a" | "b" | "c" | "d";

export const THEMES: Array<{
  id: ThemeId;
  label: string;
  hint: string;
  swatch: string;
}> = [
  { id: "a", label: "A · Indigo", hint: "Current / Linear-like", swatch: "#6e5ae6" },
  { id: "b", label: "B · Teal", hint: "Ops / terminal", swatch: "#2dd4bf" },
  { id: "c", label: "C · Copper", hint: "Editorial warm", swatch: "#c4783a" },
  { id: "d", label: "D · Blue", hint: "GitHub-native", swatch: "#58a6ff" },
];

const STORAGE_KEY = "selfpi-lab-theme";

interface ThemeContextValue {
  theme: ThemeId;
  setTheme: (id: ThemeId) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeId | null;
    return stored && THEMES.some((t) => t.id === stored) ? stored : "a";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((id: ThemeId) => setThemeState(id), []);

  const value = useMemo(() => ({ theme, setTheme }), [theme, setTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

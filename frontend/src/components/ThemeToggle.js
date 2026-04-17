"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-10 h-10 rounded-full glass-panel flex items-center justify-center pointer-events-none opacity-0">
        <Sun size={18} />
      </div>
    );
  }

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full glass-panel flex items-center justify-center text-text-primary hover:scale-110 transition-transform duration-300 shadow-lg border border-border group overflow-hidden"
      aria-label="Toggle Dark Mode"
    >
      <div className="relative w-full h-full flex items-center justify-center">
        <div className={`absolute transition-all duration-500 ease-in-out transform ${theme === 'dark' ? 'opacity-0 scale-50 rotate-90' : 'opacity-100 scale-100 rotate-0'}`}>
          <Sun size={20} className="text-[#c19275]" />
        </div>
        <div className={`absolute transition-all duration-500 ease-in-out transform ${theme === 'light' ? 'opacity-0 scale-50 -rotate-90' : 'opacity-100 scale-100 rotate-0'}`}>
          <Moon size={20} className="text-[#e1c6b5]" />
        </div>
      </div>
    </button>
  );
}

import { useState } from "react";
import { Moon, Sun } from "lucide-react";

export default function LandingPage({ onAnalyze, isDark, onToggleTheme }) {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    const trimmed = input.trim().toUpperCase();
    if (trimmed) onAnalyze(trimmed);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSubmit();
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-5 bg-background">
      <button
        className="fixed top-8 right-8 text-text-dim hover:text-on-surface transition-colors p-2 z-50"
        onClick={onToggleTheme}
        aria-label="Toggle theme"
      >
        {isDark ? <Moon className="w-6 h-6" /> : <Sun className="w-6 h-6" />}
      </button>

      <div className="text-center w-full max-w-[520px]">
        <h1 className="font-data-lg text-4xl tracking-widest uppercase mb-2 text-on-surface">
          DELTADCF
        </h1>
        <p className="font-data-sm text-data-sm text-text-dim mb-8">
          AI-powered DCF analysis and management audit.
        </p>

        <div className="relative w-full flex items-center bg-background border border-border-terminal">
          <input
            className="ticker-input w-full bg-transparent border-none text-on-surface font-data-md text-data-md h-12 px-4 placeholder:text-text-dim"
            placeholder="Enter ticker... e.g. AAPL, ETERNAL.NS"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
          />
          <button
            className="bg-action-blue text-white font-data-md text-data-md px-6 h-12 whitespace-nowrap hover:bg-blue-600 transition-colors"
            onClick={handleSubmit}
          >
            ANALYZE →
          </button>
        </div>
      </div>
    </div>
  );
}

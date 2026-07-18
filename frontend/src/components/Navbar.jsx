import { useState } from "react";
import { Moon, Sun } from "lucide-react";

export default function Navbar({
  tickerInput,
  onTickerInputChange,
  onSubmit,
  onLogoClick,
  isSubmitting,
  isDark,
  onToggleTheme,
}) {
  const [flash, setFlash] = useState(false);

  const handleSubmit = () => {
    if (isSubmitting) return;
    setFlash(true);
    setTimeout(() => setFlash(false), 150);
    onSubmit();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !isSubmitting) handleSubmit();
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-14 flex items-center justify-between px-5 bg-background border-b border-border-terminal z-50">
      <div
        className="flex items-center gap-8 w-48 cursor-pointer"
        onClick={onLogoClick}
      >
        <span className="font-data-lg text-xl tracking-widest uppercase text-on-surface">
          DELTADCF
        </span>
      </div>

      <div className="flex flex-1 max-w-2xl mx-10">
        <div className="relative w-full flex items-center bg-background border border-border-terminal">
          <input
            className="ticker-input w-full bg-transparent border-none text-on-surface font-data-md text-data-md h-9 px-3 placeholder:text-text-dim"
            placeholder="Enter ticker... e.g. AAPL, NVDA"
            type="text"
            value={tickerInput}
            onChange={(e) => onTickerInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSubmitting}
          />
          <button
            className={`font-data-md text-data-md px-4 h-9 whitespace-nowrap transition-colors ${
              flash
                ? "bg-white text-black"
                : "bg-action-blue text-white hover:bg-blue-600"
            }`}
            onClick={handleSubmit}
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting ? "ANALYZING…" : "ANALYZE →"}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-end w-48">
        <button
          className="text-text-dim hover:text-on-surface transition-colors p-2"
          onClick={onToggleTheme}
          aria-label="Toggle theme"
        >
          {isDark ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
        </button>
      </div>
    </header>
  );
}

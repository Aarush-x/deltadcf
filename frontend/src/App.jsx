import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import LandingPage from "./components/LandingPage";
import AnalysisPage from "./components/AnalysisPage";

async function fetchAnalysis(ticker) {
  const res = await fetch(`http://localhost:8000/api/analyze/${ticker}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json();
}

export default function App() {
  const [page, setPage] = useState("landing");
  const [ticker, setTicker] = useState("");
  const [tickerInput, setTickerInput] = useState("");
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("deltadcf-theme");
    const dark = saved !== "light";
    setIsDark(dark);
    document.documentElement.classList.toggle("dark", dark);
    document.documentElement.classList.toggle("light", !dark);
  }, []);

  const toggleTheme = () => {
    setIsDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      document.documentElement.classList.toggle("light", !next);
      localStorage.setItem("deltadcf-theme", next ? "dark" : "light");
      return next;
    });
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["analysis", ticker],
    queryFn: () => fetchAnalysis(ticker),
    enabled: !!ticker,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const handleAnalyze = (value) => {
    const trimmed = value.trim().toUpperCase();
    if (!trimmed) return;
    setTicker(trimmed);
    setTickerInput(trimmed);
    setPage("analysis");
  };

  const handleSubmit = () => {
    handleAnalyze(tickerInput);
  };

  const handleLogoClick = () => {
    setPage("landing");
    setTicker("");
    setTickerInput("");
  };

  if (page === "landing") {
    return (
      <LandingPage
        onAnalyze={handleAnalyze}
        isDark={isDark}
        onToggleTheme={toggleTheme}
      />
    );
  }

  return (
    <AnalysisPage
      ticker={ticker}
      tickerInput={tickerInput}
      onTickerInputChange={setTickerInput}
      onSubmit={handleSubmit}
      onLogoClick={handleLogoClick}
      data={data}
      isLoading={isLoading}
      isError={isError}
      error={error}
      isDark={isDark}
      onToggleTheme={toggleTheme}
    />
  );
}

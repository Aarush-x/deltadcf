import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import LandingPage from "./components/LandingPage";
import AnalysisPage from "./components/AnalysisPage";

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();

if (import.meta.env.PROD && !configuredApiUrl) {
  throw new Error("VITE_API_URL is required for production builds");
}

const developmentApiUrl = import.meta.env.DEV ? "http://localhost:8000" : "";
const API_BASE_URL = (configuredApiUrl || developmentApiUrl).replace(/\/+$/, "");
const REQUEST_TIMEOUT_MS = 120_000;

function errorMessageForStatus(status) {
  if (status === 404 || status === 422) {
    return "That ticker could not be analyzed. Enter a valid S&P 500 symbol.";
  }
  if (status === 429) {
    return "The service is receiving too many requests. Wait a moment and try again.";
  }
  if (status === 503) {
    return "A financial-data or AI provider is temporarily unavailable. Try again later.";
  }
  if (status >= 500) {
    return "The analysis service encountered an error. Try again later.";
  }
  return "The analysis request could not be completed.";
}

async function fetchAnalysis(ticker, querySignal) {
  const timeoutController = new AbortController();
  const timeoutId = window.setTimeout(
    () => timeoutController.abort("timeout"),
    REQUEST_TIMEOUT_MS,
  );
  const cancelFromQuery = () => timeoutController.abort("cancelled");
  querySignal?.addEventListener("abort", cancelFromQuery, { once: true });

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/analyze/${encodeURIComponent(ticker)}`,
      { signal: timeoutController.signal },
    );
    if (!response.ok) {
      throw new Error(errorMessageForStatus(response.status));
    }
    return await response.json();
  } catch (error) {
    if (timeoutController.signal.aborted) {
      if (timeoutController.signal.reason === "timeout") {
        throw new Error("The analysis timed out. Try again in a moment.");
      }
      throw new Error("The analysis request was cancelled.");
    }
    if (error instanceof TypeError) {
      throw new Error("The analysis service is unreachable. Check your connection and try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
    querySignal?.removeEventListener("abort", cancelFromQuery);
  }
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

  const { data, isLoading, isFetching, isError, error } = useQuery({
    queryKey: ["analysis", ticker],
    queryFn: ({ signal }) => fetchAnalysis(ticker, signal),
    enabled: !!ticker,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const handleAnalyze = (value) => {
    if (isFetching) return;
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
      isSubmitting={isFetching}
      isDark={isDark}
      onToggleTheme={toggleTheme}
    />
  );
}

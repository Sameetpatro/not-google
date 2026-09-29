import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import {
  Search,
  X,
  Sparkles,
  Globe,
  Settings,
  ShieldCheck,
  ChevronRight,
  ExternalLink,
  Moon,
  Sun,
  MoreVertical,
  Check,
  Copy,
  Clock,
  ArrowRight,
  Bookmark,
  Share2,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Layers,
  Database,
  Terminal,
} from "lucide-react";


function GoogleAppsGridIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <circle cx="5" cy="5" r="2" />
      <circle cx="12" cy="5" r="2" />
      <circle cx="19" cy="5" r="2" />
      <circle cx="5" cy="12" r="2" />
      <circle cx="12" cy="12" r="2" />
      <circle cx="19" cy="12" r="2" />
      <circle cx="5" cy="19" r="2" />
      <circle cx="12" cy="19" r="2" />
      <circle cx="19" cy="19" r="2" />
    </svg>
  );
}

function GoogleSparkleIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <path
        d="M12 2L14.2 8.2L20.4 10.4L14.2 12.6L12 18.8L9.8 12.6L3.6 10.4L9.8 8.2L12 2Z"
        fill="url(#notgoogle-sge-sparkle)"
      />
      <defs>
        <linearGradient id="notgoogle-sge-sparkle" x1="3.6" y1="2" x2="20.4" y2="18.8" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4285F4" />
          <stop offset="0.33" stopColor="#9B51E0" />
          <stop offset="0.66" stopColor="#EA4335" />
          <stop offset="1" stopColor="#FBBC05" />
        </linearGradient>
      </defs>
    </svg>
  );
}

// --- NotGoogle Logo Component ---
function NotGoogleLogo({ size = "large", onClick }) {
  const letters = [
    { char: "N", color: "#4285F4" }, // Blue
    { char: "o", color: "#EA4335" }, // Red
    { char: "t", color: "#FBBC05" }, // Yellow
    { char: "G", color: "#4285F4" }, // Blue
    { char: "o", color: "#34A853" }, // Green
    { char: "o", color: "#EA4335" }, // Red
    { char: "g", color: "#4285F4" }, // Blue
    { char: "l", color: "#34A853" }, // Green
    { char: "e", color: "#EA4335" }, // Red
  ];

  if (size === "small") {
    return (
      <div
        onClick={onClick}
        title="Go to NotGoogle Home"
        className="font-product font-medium text-[26px] tracking-[-0.04em] select-none cursor-pointer flex items-center transition-transform hover:scale-105"
      >
        {letters.map((item, idx) => (
          <span key={idx} style={{ color: item.color }}>
            {item.char}
          </span>
        ))}
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className="font-product font-medium text-7xl sm:text-8xl md:text-[90px] tracking-[-0.04em] select-none flex items-center justify-center cursor-pointer transition-transform hover:scale-[1.01]"
    >
      {letters.map((item, idx) => (
        <span key={idx} style={{ color: item.color }}>
          {item.char}
        </span>
      ))}
    </div>
  );
}

// --- Main App ---
export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchResponse, setSearchResponse] = useState(null);
  const [searchDuration, setSearchDuration] = useState("0.24");

  // User Settings & Toggles
  const [aiOverviewToggle, setAiOverviewToggle] = useState(true);
  const [searxngToggle, setSearxngToggle] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState("all"); // 'all', 'ai', 'web'
  const [showAppsMenu, setShowAppsMenu] = useState(false);
  const [showCrawlerModal, setShowCrawlerModal] = useState(false);
  const [seedKeyword, setSeedKeyword] = useState("");
  const [seedLoading, setSeedLoading] = useState(false);
  const [crawlerStats, setCrawlerStats] = useState(null);

  const inputRef = useRef(null);

  // Sync theme with HTML class
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  // Continuously poll crawler status every 3 seconds
  useEffect(() => {
    const fetchStatus = () => {
      fetch("http://localhost:8000/crawler/status")
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) setCrawlerStats(data);
        })
        .catch(() => {});
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSeedCrawler = async (e) => {
    e.preventDefault();
    if (!seedKeyword.trim()) return;
    setSeedLoading(true);
    try {
      await fetch("http://localhost:8000/crawler/seed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keywords: [seedKeyword.trim()] }),
      });
      setSeedKeyword("");
      // Fetch status immediately
      const res = await fetch("http://localhost:8000/crawler/status");
      if (res.ok) setCrawlerStats(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setSeedLoading(false);
    }
  };

  const handleSearch = async (e, forcedQuery = null) => {
    if (e) e.preventDefault();
    const targetQuery = (forcedQuery !== null ? forcedQuery : query).trim();
    if (!targetQuery) return;

    if (forcedQuery !== null) {
      setQuery(forcedQuery);
    }

    setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      const params = new URLSearchParams({
        q: targetQuery,
        ai_overview: aiOverviewToggle.toString(),
        include_searxng: searxngToggle.toString(),
      });

      const res = await fetch(`http://localhost:8000/search?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP error: ${res.status}`);

      const data = await res.json();
      setSearchResponse(data);
      const totalTime = ((performance.now() - startTime) / 1000).toFixed(2);
      setSearchDuration(totalTime);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      console.error(err);
      setError("Failed to fetch search results. Verify FastAPI is active on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  const handleFeelingLucky = () => {
    const luckyList = [
      "fastapi",
      "python web framework",
      "cross-encoder reranking",
      "vector store pgvector",
      "zero telemetry privacy",
    ];
    const picked = luckyList[Math.floor(Math.random() * luckyList.length)];
    handleSearch(null, picked);
  };

  const resetToHome = () => {
    setSearchResponse(null);
    setQuery("");
    setError(null);
    if (inputRef.current) inputRef.current.focus();
  };

  const scrollToSource = (citationId) => {
    const el = document.getElementById(`source-card-${citationId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("highlight-source", "ring-2", "ring-[#4285F4]");
      setTimeout(() => {
        el.classList.remove("highlight-source", "ring-2", "ring-[#4285F4]");
      }, 2500);
    }
  };

  return (
    <div
      className={`min-h-screen flex flex-col font-sans transition-colors duration-150 ${
        darkMode ? "bg-[#202124] text-[#e8eaed]" : "bg-white text-[#202124]"
      }`}
    >


      {/* Crawler Live Monitor & Topic Seeder Modal */}
      {showCrawlerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div
            className={`w-full max-w-lg p-6 rounded-3xl shadow-2xl space-y-5 animate-in fade-in zoom-in-95 border ${
              darkMode ? "bg-[#303134] border-[#3c4043] text-white" : "bg-white border-[#dadce0] text-gray-900"
            }`}
          >
            <div className="flex justify-between items-center pb-3 border-b border-inherit">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <h3 className="font-product text-lg font-semibold">Continuous Crawler & Indexer</h3>
              </div>
              <button
                onClick={() => setShowCrawlerModal(false)}
                className="p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Live Stats Grid */}
            <div className="grid grid-cols-2 gap-3 text-left">
              <div className={`p-3 rounded-2xl border ${darkMode ? "bg-[#202124] border-gray-700" : "bg-gray-50 border-gray-200"}`}>
                <p className="text-xs text-gray-400">Corpus Indexed Docs</p>
                <p className="text-2xl font-bold font-mono text-[#4285F4] mt-1">
                  {crawlerStats?.indexed_corpus_docs ?? 0}
                </p>
              </div>

              <div className={`p-3 rounded-2xl border ${darkMode ? "bg-[#202124] border-gray-700" : "bg-gray-50 border-gray-200"}`}>
                <p className="text-xs text-gray-400">Discovered Frontier Queue</p>
                <p className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                  {crawlerStats?.queue_size ?? 0}
                </p>
              </div>

              <div className={`p-3 rounded-2xl border ${darkMode ? "bg-[#202124] border-gray-700" : "bg-gray-50 border-gray-200"}`}>
                <p className="text-xs text-gray-400">Total URLs Seen</p>
                <p className="text-lg font-bold font-mono text-gray-300 mt-1">
                  {crawlerStats?.total_seen_urls ?? 0}
                </p>
              </div>

              <div className={`p-3 rounded-2xl border ${darkMode ? "bg-[#202124] border-gray-700" : "bg-gray-50 border-gray-200"}`}>
                <p className="text-xs text-gray-400">Status</p>
                <p className="text-sm font-semibold text-emerald-400 mt-2 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  {crawlerStats?.is_running ? "Crawling 24/7" : "Active"}
                </p>
              </div>
            </div>

            {/* Seed Topic Form */}
            <form onSubmit={handleSeedCrawler} className="space-y-3 pt-2">
              <label className="text-xs font-medium text-gray-400 block text-left">
                Broaden Domain: Seed new keyword or starting URL
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={seedKeyword}
                  onChange={(e) => setSeedKeyword(e.target.value)}
                  placeholder="e.g. quantum physics, spacex, react, machine learning..."
                  className={`flex-1 rounded-xl px-4 py-2 text-xs border outline-none ${
                    darkMode ? "bg-[#202124] border-gray-700 text-white" : "bg-gray-50 border-gray-300 text-gray-900"
                  }`}
                />
                <button
                  type="submit"
                  disabled={seedLoading || !seedKeyword.trim()}
                  className="bg-[#4285F4] hover:bg-[#3367d6] disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-xl transition"
                >
                  {seedLoading ? "Seeding..." : "Seed & Crawl"}
                </button>
              </div>
              <p className="text-[11px] text-gray-500 text-left">
                Every search query also automatically enqueues and indexes newly discovered websites in the background.
              </p>
            </form>
          </div>
        </div>
      )}

      {/* Google Apps Launcher Popover */}
      {showAppsMenu && (
        <div
          className={`fixed top-16 right-16 z-50 w-80 p-4 rounded-3xl shadow-2xl border grid grid-cols-3 gap-3 animate-in fade-in zoom-in-95 ${
            darkMode ? "bg-[#303134] border-[#3c4043] text-white" : "bg-white border-[#dadce0] text-gray-900"
          }`}
        >
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              resetToHome();
              setShowAppsMenu(false);
            }}
            className="flex flex-col items-center p-3 rounded-2xl hover:bg-black/5 dark:hover:bg-white/5 transition text-center"
          >
            <span className="w-10 h-10 rounded-full flex items-center justify-center bg-[#4285F4]/10 text-[#4285F4]">
              <Search className="w-5 h-5" />
            </span>
            <span className="text-xs mt-2 font-medium">Search</span>
          </a>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex flex-col items-center p-3 rounded-2xl hover:bg-black/5 dark:hover:bg-white/5 transition text-center"
          >
            <span className="w-10 h-10 rounded-full flex items-center justify-center bg-[#34A853]/10 text-[#34A853]">
              <Terminal className="w-5 h-5" />
            </span>
            <span className="text-xs mt-2 font-medium">API Docs</span>
          </a>

          <div
            onClick={() => {
              setAiOverviewToggle(!aiOverviewToggle);
              setShowAppsMenu(false);
            }}
            className="flex flex-col items-center p-3 rounded-2xl hover:bg-black/5 dark:hover:bg-white/5 transition text-center cursor-pointer"
          >
            <span className="w-10 h-10 rounded-full flex items-center justify-center bg-[#EA4335]/10 text-[#EA4335]">
              <GoogleSparkleIcon className="w-5 h-5" />
            </span>
            <span className="text-xs mt-2 font-medium">AI SGE</span>
          </div>

          <div
            onClick={() => {
              setSearxngToggle(!searxngToggle);
              setShowAppsMenu(false);
            }}
            className="flex flex-col items-center p-3 rounded-2xl hover:bg-black/5 dark:hover:bg-white/5 transition text-center cursor-pointer"
          >
            <span className="w-10 h-10 rounded-full flex items-center justify-center bg-[#FBBC05]/10 text-[#FBBC05]">
              <Globe className="w-5 h-5" />
            </span>
            <span className="text-xs mt-2 font-medium">SearXNG</span>
          </div>

          <a
            href="http://localhost:8000/health"
            target="_blank"
            rel="noreferrer"
            className="flex flex-col items-center p-3 rounded-2xl hover:bg-black/5 dark:hover:bg-white/5 transition text-center"
          >
            <span className="w-10 h-10 rounded-full flex items-center justify-center bg-[#4285F4]/10 text-[#4285F4]">
              <Database className="w-5 h-5" />
            </span>
            <span className="text-xs mt-2 font-medium">Health</span>
          </a>

          <div
            onClick={() => setShowAppsMenu(false)}
            className="flex flex-col items-center p-3 rounded-2xl hover:bg-black/5 dark:hover:bg-white/5 transition text-center cursor-pointer"
          >
            <span className="w-10 h-10 rounded-full flex items-center justify-center bg-[#34A853]/10 text-[#34A853]">
              <ShieldCheck className="w-5 h-5" />
            </span>
            <span className="text-xs mt-2 font-medium">Privacy</span>
          </div>
        </div>
      )}

      {/* =========================================================================
          VIEW 1: GOOGLE HOME VIEW (No search executed)
         ========================================================================= */}
      {!searchResponse ? (
        <div className="flex-1 flex flex-col justify-between">
          {/* Home Header */}
          <header className="flex items-center justify-between px-6 py-4 text-sm">
            <div className="flex items-center gap-4 text-xs font-normal">
              <span className="text-gray-500 dark:text-gray-400 hover:underline cursor-pointer">About</span>
              <button
                type="button"
                onClick={() => setShowCrawlerModal(true)}
                title="Click to view live crawler metrics and seed new topics"
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition border border-emerald-500/20 cursor-pointer"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>{crawlerStats ? `${crawlerStats.indexed_corpus_docs || crawlerStats.pages_indexed || 0} Docs Indexed` : "Crawler Active"}</span>
              </button>
            </div>

            <div className="flex items-center gap-4">
              <span
                onClick={() => setSearxngToggle(!searxngToggle)}
                className="text-xs font-medium cursor-pointer hover:underline text-gray-600 dark:text-gray-300"
              >
                SearXNG {searxngToggle ? "✓" : "○"}
              </span>

              {/* Theme Toggle */}
              <button
                type="button"
                onClick={() => setDarkMode(!darkMode)}
                title="Toggle Theme"
                className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition text-gray-600 dark:text-gray-300"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* Google App Grid */}
              <button
                type="button"
                onClick={() => setShowAppsMenu(!showAppsMenu)}
                title="NotGoogle apps"
                className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition text-gray-600 dark:text-gray-300"
              >
                <GoogleAppsGridIcon className="w-5 h-5" />
              </button>

              {/* Google User Avatar */}
              <div
                title="Google Account: Privacy Guard Active"
                className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#4285F4] to-[#34A853] p-[2px] cursor-pointer"
              >
                <div className="w-full h-full rounded-full bg-[#202124] flex items-center justify-center text-white text-xs font-semibold">
                  N
                </div>
              </div>
            </div>
          </header>

          {/* Home Center Body */}
          <main className="flex flex-col items-center justify-center px-4 max-w-3xl mx-auto w-full -mt-16">
            <NotGoogleLogo size="large" onClick={resetToHome} />

            {/* Google Search Bar Pill */}
            <form onSubmit={handleSearch} className="w-full mt-7">
              <div
                className={`relative flex items-center w-full rounded-full border transition-all duration-200 px-4 py-3 shadow-sm hover:shadow-md focus-within:shadow-md ${
                  darkMode
                    ? "bg-[#202124] border-[#5f6368] hover:bg-[#303134] focus-within:bg-[#303134] focus-within:border-transparent"
                    : "bg-white border-[#dfe1e5] hover:border-transparent focus-within:border-transparent"
                }`}
              >
                <Search className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />

                <input
                  ref={inputRef}
                  type="text"
                  autoFocus
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search NotGoogle or type a URL"
                  className={`w-full bg-transparent text-base outline-none pr-3 ${
                    darkMode ? "text-white placeholder-gray-400" : "text-gray-900 placeholder-gray-500"
                  }`}
                />

                {query && (
                  <button
                    type="button"
                    onClick={() => {
                      setQuery("");
                      inputRef.current?.focus();
                    }}
                    className="p-1 mr-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Google Search Buttons */}
              <div className="flex items-center justify-center gap-3 mt-7">
                <button
                  type="submit"
                  disabled={loading}
                  className={`px-4 py-2 text-sm rounded-md border font-normal transition ${
                    darkMode
                      ? "bg-[#303134] text-[#e8eaed] border-[#303134] hover:border-[#5f6368]"
                      : "bg-[#f8f9fa] text-[#3c4043] border-[#f8f9fa] hover:border-[#dadce0] hover:bg-[#f8f9fa]"
                  }`}
                >
                  {loading ? "Searching..." : "NotGoogle Search"}
                </button>

                <button
                  type="button"
                  onClick={handleFeelingLucky}
                  className={`px-4 py-2 text-sm rounded-md border font-normal transition ${
                    darkMode
                      ? "bg-[#303134] text-[#e8eaed] border-[#303134] hover:border-[#5f6368]"
                      : "bg-[#f8f9fa] text-[#3c4043] border-[#f8f9fa] hover:border-[#dadce0] hover:bg-[#f8f9fa]"
                  }`}
                >
                  I'm Feeling Lucky
                </button>
              </div>

              {/* Google Language & Feature Pills */}
              <div className="flex flex-col items-center gap-3 mt-6 text-xs text-gray-500 dark:text-gray-400">
                <p>
                  NotGoogle offered in:{" "}
                  <span className="text-[#4285F4] hover:underline cursor-pointer">English</span> ·{" "}
                  <span className="text-[#4285F4] hover:underline cursor-pointer">Privacy Mode</span> ·{" "}
                  <span className="text-[#4285F4] hover:underline cursor-pointer">Zero Telemetry</span>
                </p>

                <div className="flex items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setAiOverviewToggle(!aiOverviewToggle)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium transition ${
                      aiOverviewToggle
                        ? darkMode
                          ? "bg-blue-950/60 text-blue-300 border-blue-700"
                          : "bg-blue-50 text-blue-700 border-blue-200"
                        : "bg-transparent text-gray-400 border-gray-400/40 hover:text-gray-200"
                    }`}
                  >
                    <GoogleSparkleIcon className="w-3.5 h-3.5" />
                    AI Overview (SGE)
                  </button>

                  <button
                    type="button"
                    onClick={() => setSearxngToggle(!searxngToggle)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium transition ${
                      searxngToggle
                        ? darkMode
                          ? "bg-emerald-950/60 text-emerald-300 border-emerald-700"
                          : "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-transparent text-gray-400 border-gray-400/40 hover:text-gray-200"
                    }`}
                  >
                    <Globe className="w-3.5 h-3.5 text-[#34A853]" />
                    SearXNG Web
                  </button>
                </div>
              </div>
            </form>
          </main>

          {/* Google Home Footer */}
          <footer
            className={`w-full text-xs font-normal border-t ${
              darkMode ? "bg-[#171717] border-[#3c4043] text-[#9aa0a6]" : "bg-[#f2f2f2] border-[#dadce0] text-[#70757a]"
            }`}
          >
            <div className="px-6 py-3 border-b border-inherit">
              <span>India · From your network address · Protected by NotGoogle PII Boundary</span>
            </div>
            <div className="px-6 py-3 flex flex-wrap items-center justify-between gap-y-2">
              <div className="flex items-center gap-6">
                <span className="hover:underline cursor-pointer">About</span>
                <span className="hover:underline cursor-pointer">Advertising</span>
                <span className="hover:underline cursor-pointer">Business</span>
                <span className="hover:underline cursor-pointer">How Search Works</span>
              </div>
              <div className="flex items-center gap-6">
                <span className="hover:underline cursor-pointer">Privacy Shield Active</span>
                <span className="hover:underline cursor-pointer">Terms</span>
                <span className="hover:underline cursor-pointer">Settings</span>
              </div>
            </div>
          </footer>
        </div>
      ) : (
        /* =========================================================================
            VIEW 2: GOOGLE RESULTS VIEW (Google Search Engine Results Page)
           ========================================================================= */
        <div className="flex-1 flex flex-col">
          {/* Google Results Top Sticky Bar */}
          <header
            className={`sticky top-0 z-30 border-b px-4 sm:px-6 pt-4 pb-0 backdrop-blur-md transition-colors ${
              darkMode ? "bg-[#202124]/95 border-[#3c4043]" : "bg-white/95 border-[#dadce0]"
            }`}
          >
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
              {/* Logo & Compact Search Pill */}
              <div className="flex items-center gap-6 flex-1 max-w-3xl">
                <NotGoogleLogo size="small" onClick={resetToHome} />

                {/* Compact Search Bar */}
                <form onSubmit={handleSearch} className="flex-1 relative">
                  <div
                    className={`flex items-center w-full rounded-full border transition-all duration-200 px-4 py-2.5 shadow-sm hover:shadow-md focus-within:shadow-md ${
                      darkMode
                        ? "bg-[#303134] border-transparent hover:bg-[#303134] focus-within:bg-[#303134]"
                        : "bg-white border-[#dfe1e5] hover:border-transparent focus-within:border-transparent"
                    }`}
                  >
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Search NotGoogle or type a URL"
                      className={`w-full bg-transparent text-sm outline-none pr-2 ${
                        darkMode ? "text-white" : "text-gray-900"
                      }`}
                    />

                    {query && (
                      <button
                        type="button"
                        onClick={() => setQuery("")}
                        className="p-1 mr-1 text-gray-400 hover:text-gray-200"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}

                    <button
                      type="submit"
                      disabled={loading}
                      title="Search"
                      className="p-1.5 text-[#4285F4] hover:opacity-80 transition pl-2 border-l border-gray-300 dark:border-gray-600"
                    >
                      <Search className="w-4 h-4" />
                    </button>
                  </div>
                </form>
              </div>

              {/* Right Action Icons */}
              <div className="flex items-center gap-3">
                {/* AI Overview Toggle Button */}
                <button
                  type="button"
                  onClick={() => setAiOverviewToggle(!aiOverviewToggle)}
                  title="Toggle AI Overview (SGE)"
                  className={`hidden sm:flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border transition ${
                    aiOverviewToggle
                      ? darkMode
                        ? "bg-blue-950 text-blue-300 border-blue-700"
                        : "bg-blue-50 text-blue-700 border-blue-200"
                      : "bg-transparent text-gray-400 border-gray-600"
                  }`}
                >
                  <GoogleSparkleIcon className="w-3.5 h-3.5" />
                  SGE {aiOverviewToggle ? "On" : "Off"}
                </button>

                {/* Crawler Status Pill */}
                <button
                  type="button"
                  onClick={() => setShowCrawlerModal(true)}
                  title="Click to view live crawler metrics and seed new topics"
                  className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition border border-emerald-500/20 text-xs cursor-pointer"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>{crawlerStats ? `${crawlerStats.indexed_corpus_docs || crawlerStats.pages_indexed || 0} Docs` : "Crawler"}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setDarkMode(!darkMode)}
                  title="Toggle Theme"
                  className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition text-gray-400 hover:text-gray-200"
                >
                  {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </button>

                <button
                  type="button"
                  onClick={() => setShowAppsMenu(!showAppsMenu)}
                  title="NotGoogle Apps"
                  className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition text-gray-400 hover:text-gray-200"
                >
                  <GoogleAppsGridIcon className="w-4 h-4" />
                </button>

                <div
                  title="Profile: NotGoogle User"
                  className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#4285F4] to-[#EA4335] p-[2px] cursor-pointer"
                >
                  <div className="w-full h-full rounded-full bg-[#202124] flex items-center justify-center text-white text-xs font-bold">
                    N
                  </div>
                </div>
              </div>
            </div>

            {/* Google Results Tabs Navigation */}
            <div className="max-w-7xl mx-auto flex items-center justify-between text-xs font-medium pt-3 text-gray-500 dark:text-gray-400 overflow-x-auto no-scrollbar">
              <div className="flex items-center gap-6">
                <button
                  onClick={() => setActiveTab("all")}
                  className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition ${
                    activeTab === "all"
                      ? "text-[#4285F4] border-[#4285F4] font-semibold"
                      : "border-transparent hover:text-gray-300"
                  }`}
                >
                  <Search className="w-3.5 h-3.5" />
                  All
                </button>

                <button
                  onClick={() => setActiveTab("ai")}
                  className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition ${
                    activeTab === "ai"
                      ? "text-[#4285F4] border-[#4285F4] font-semibold"
                      : "border-transparent hover:text-gray-300"
                  }`}
                >
                  <GoogleSparkleIcon className="w-3.5 h-3.5" />
                  AI Overview
                </button>

                <button
                  onClick={() => setActiveTab("web")}
                  className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition ${
                    activeTab === "web"
                      ? "text-[#4285F4] border-[#4285F4] font-semibold"
                      : "border-transparent hover:text-gray-300"
                  }`}
                >
                  <Globe className="w-3.5 h-3.5" />
                  Web (SearXNG)
                </button>

              </div>

              <div className="flex items-center gap-4 pb-2.5">
                <span className="text-emerald-400 flex items-center gap-1.5 text-xs font-mono">
                  <ShieldCheck className="w-3.5 h-3.5" /> PII Scrubbed
                </span>
              </div>
            </div>
          </header>


          {/* Results Main Container */}
          <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-4 flex-1">
            {/* Search Metadata Line */}
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-4 pl-0 sm:pl-2">
              About {searchResponse.total_res || 0} results ({searchDuration} seconds)
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
                {error}
              </div>
            )}

            {/* Layout Grid: Organic Column + SearXNG Knowledge Sidebar */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Left Main Column: SGE Box + Organic Results */}
              <div className={`${searchResponse.searxng_resp && searxngToggle ? "lg:col-span-8" : "lg:col-span-9 max-w-3xl"} space-y-6`}>
                {/* -------------------------------------------------------------
                    GOOGLE SGE (SEARCH GENERATIVE EXPERIENCE) CARD
                   ------------------------------------------------------------- */}
                {searchResponse.ai_overview && (activeTab === "all" || activeTab === "ai") && (
                  <section
                    className={`rounded-2xl border p-5 shadow-sm relative overflow-hidden transition-all ${
                      darkMode
                        ? "bg-[#252830] border-[#3c4043] text-gray-200"
                        : "bg-[#f8fafd] border-[#dadce0] text-gray-800"
                    }`}
                  >
                    {/* SGE Header */}
                    <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700/60">
                      <div className="flex items-center gap-2">
                        <GoogleSparkleIcon className="w-5 h-5" />
                        <h2 className="text-base font-product font-semibold tracking-tight">AI Overview</h2>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/20">
                          SGE Experimental
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <button title="Helpful" className="p-1 rounded hover:bg-black/5 dark:hover:bg-white/10">
                          <ThumbsUp className="w-3.5 h-3.5" />
                        </button>
                        <button title="Not helpful" className="p-1 rounded hover:bg-black/5 dark:hover:bg-white/10">
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* SGE Content */}
                    <div className="prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed space-y-2">
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="mb-2.5 leading-6">{children}</p>,
                          strong: ({ children }) => <strong className="font-semibold text-[#4285F4] dark:text-[#8ab4f8]">{children}</strong>,
                          ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 mb-3">{children}</ul>,
                          li: ({ children }) => <li className="leading-6">{children}</li>,
                        }}
                      >
                        {searchResponse.ai_overview.markdown_text}
                      </ReactMarkdown>
                    </div>

                    {/* SGE Source Carousel Chips */}
                    {searchResponse.ai_overview.sources?.length > 0 && (
                      <div className="mt-5 pt-3 border-t border-gray-200 dark:border-gray-700/60">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                            Sources used for overview:
                          </span>
                        </div>
                        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
                          {searchResponse.ai_overview.sources.map((src) => (
                            <button
                              key={src.citation_id}
                              onClick={() => scrollToSource(src.citation_id)}
                              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs text-left transition flex-shrink-0 max-w-[220px] ${
                                darkMode
                                  ? "bg-[#303134] border-[#3c4043] hover:border-[#8ab4f8] text-gray-200"
                                  : "bg-white border-[#dfe1e5] hover:border-[#1a73e8] text-gray-800 shadow-sm"
                              }`}
                            >
                              <span className="w-5 h-5 rounded-full bg-[#4285F4]/10 text-[#4285F4] font-bold text-[10px] flex items-center justify-center flex-shrink-0">
                                {src.citation_id}
                              </span>
                              <div className="truncate">
                                <p className="font-medium truncate">{src.title}</p>
                                <p className="text-[10px] text-gray-400 truncate">{src.url}</p>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </section>
                )}

                {/* -------------------------------------------------------------
                    ORGANIC SEARCH RESULTS (Google Standard Result List)
                   ------------------------------------------------------------- */}
                {(activeTab === "all" || activeTab === "ai") && (
                  <div className="space-y-6 pt-1">
                    {searchResponse.resp?.length === 0 ? (
                      <div className="py-8 text-center text-gray-500 text-sm">
                        No indexed local documents found for <strong className="text-gray-300">"{query}"</strong>.
                        <p className="mt-1 text-xs">Try broadening your query or inspect the SearXNG web aggregate.</p>
                      </div>
                    ) : (
                      searchResponse.resp?.map((item, idx) => (
                        <GoogleOrganicResultItem key={item.id || idx} item={item} darkMode={darkMode} />
                      ))
                    )}
                  </div>
                )}

                {/* Tab: Web Only (SearXNG Results in main column if activeTab === 'web') */}
                {activeTab === "web" && (
                  <div className="space-y-6 pt-1">
                    <h3 className="text-sm font-semibold flex items-center gap-2 text-emerald-500">
                      <Globe className="w-4 h-4" /> Live Web Results (SearXNG)
                    </h3>
                    {searchResponse.searxng_resp?.length === 0 ? (
                      <p className="text-xs text-gray-500 py-4">No live web results returned.</p>
                    ) : (
                      searchResponse.searxng_resp?.map((item, idx) => (
                        <GoogleOrganicResultItem key={item.id || idx} item={item} darkMode={darkMode} />
                      ))
                    )}
                  </div>
                )}

                {/* Google Pagination: "NotGooooogle" */}
                <GooglePagination query={query} onPageSelect={(p) => handleSearch(null, query)} />
              </div>

              {/* ---------------------------------------------------------------
                  RIGHT COLUMN: GOOGLE KNOWLEDGE PANEL (SearXNG Web Aggregate)
                 --------------------------------------------------------------- */}
              {searchResponse.searxng_resp && searxngToggle && activeTab === "all" && (
                <div className="lg:col-span-4 space-y-4">
                  <div
                    className={`rounded-2xl border p-5 shadow-sm ${
                      darkMode ? "bg-[#252830] border-[#3c4043]" : "bg-white border-[#dadce0]"
                    }`}
                  >
                    <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-700/60 mb-3">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-[#34A853]" />
                        <h3 className="font-product text-sm font-semibold">Web Knowledge</h3>
                      </div>
                      <span className="text-[10px] font-mono uppercase bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        SearXNG Multi-Engine
                      </span>
                    </div>

                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                      Live aggregate results queried in parallel from external web engines.
                    </p>

                    <div className="space-y-3">
                      {searchResponse.searxng_resp.slice(0, 6).map((item, idx) => (
                        <article
                          key={idx}
                          className={`p-3 rounded-xl border transition hover:border-[#4285F4] ${
                            darkMode ? "bg-[#303134]/60 border-[#3c4043]" : "bg-gray-50 border-gray-200"
                          }`}
                        >
                          <div className="flex items-center gap-2 text-[11px] text-gray-400 truncate mb-1">
                            <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center text-[9px] font-bold">
                              W
                            </span>
                            <span className="truncate">{item.url}</span>
                          </div>

                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sm font-medium text-[#1a0dab] dark:text-[#8ab4f8] hover:underline block leading-snug line-clamp-1"
                          >
                            {item.title}
                          </a>

                          <p className="text-xs text-gray-600 dark:text-[#bdc1c6] line-clamp-2 mt-1 leading-relaxed">
                            {item.snippet}
                          </p>

                          {item.source && (
                            <span className="mt-2 inline-block text-[9px] font-mono px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                              via {item.source}
                            </span>
                          )}
                        </article>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </main>

          {/* Results Footer */}
          <footer
            className={`w-full text-xs font-normal border-t mt-12 ${
              darkMode ? "bg-[#171717] border-[#3c4043] text-[#9aa0a6]" : "bg-[#f2f2f2] border-[#dadce0] text-[#70757a]"
            }`}
          >
            <div className="max-w-7xl mx-auto px-6 py-3 border-b border-inherit flex items-center gap-2">
              <span className="font-medium text-gray-400">India</span>
              <span>·</span>
              <span>Based on your network connection · Strict Privacy Enforced</span>
            </div>
            <div className="max-w-7xl mx-auto px-6 py-3 flex flex-wrap items-center justify-between gap-y-2">
              <div className="flex items-center gap-6">
                <span className="hover:underline cursor-pointer">Help</span>
                <span className="hover:underline cursor-pointer">Send feedback</span>
                <span className="hover:underline cursor-pointer">Privacy</span>
                <span className="hover:underline cursor-pointer">Terms</span>
              </div>
              <div className="flex items-center gap-4">
                <span>NotGoogle v2.4 (Search & SGE)</span>
              </div>
            </div>
          </footer>
        </div>
      )}
    </div>
  );
}

// --- Google Organic Result Item Component ---
function GoogleOrganicResultItem({ item, darkMode }) {
  // Extract a clean domain and path representation
  let domain = "";
  let pathBreadcrumb = "";
  try {
    const urlObj = new URL(item.url);
    domain = urlObj.hostname.replace("www.", "");
    pathBreadcrumb = urlObj.pathname.split("/").filter(Boolean).slice(0, 2).join(" › ");
  } catch {
    domain = item.url;
  }

  return (
    <article
      id={`source-card-${item.id}`}
      className="group max-w-2xl text-left select-text transition-all duration-200"
    >
      {/* Line 1: Favicon / Domain Breadcrumb */}
      <div className="flex items-center gap-2 mb-1">
        <div className="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-600 dark:text-gray-300 flex-shrink-0">
          {domain.charAt(0).toUpperCase()}
        </div>
        <div className="flex flex-col text-xs leading-tight truncate">
          <span className={`font-medium truncate ${darkMode ? "text-gray-300" : "text-gray-800"}`}>
            {domain}
          </span>
          <span className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
            {item.url} {pathBreadcrumb ? `› ${pathBreadcrumb}` : ""}
          </span>
        </div>
        <button
          title="More options"
          className="ml-auto opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-black/5 dark:hover:bg-white/10 transition text-gray-400"
        >
          <MoreVertical className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Line 2: Big Clickable Blue Title */}
      <h3 className="text-[20px] leading-[26px] font-normal">
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className={`hover:underline block ${
            darkMode ? "text-[#8ab4f8]" : "text-[#1a0dab]"
          }`}
        >
          {item.title}
        </a>
      </h3>

      {/* Line 3: Snippet */}
      <p className={`text-[14px] leading-[22px] mt-1 line-clamp-3 ${
        darkMode ? "text-[#bdc1c6]" : "text-[#4d5156]"
      }`}>
        {item.snippet}
      </p>

      {/* Line 4: Relevance & Ingestion Status Tag */}
      <div className="mt-1.5 flex items-center gap-2">
        {item.source === "cross_encoder" ? (
          <span className="text-[10px] font-mono text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full">
            Indexed Corpus · {Math.min(100, Math.max(1, Math.round((item.score > 1 ? item.score / 10 : item.score) * 100)))}% match
          </span>
        ) : (
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
            Live Web {item.source?.replace("searxng_", "") ? `· ${item.source.replace("searxng_", "")}` : ""}
          </span>
        )}
      </div>
    </article>

  );
}

// --- Google Pagination Component ("NotGooooogle") ---
function GooglePagination({ query, onPageSelect }) {
  return (
    <div className="flex flex-col items-center justify-center my-12 select-none">
      <div className="flex items-center text-4xl sm:text-5xl font-product tracking-wider font-medium">
        <span style={{ color: "#4285F4" }}>N</span>
        <span style={{ color: "#EA4335" }}>o</span>
        <span style={{ color: "#FBBC05" }}>t</span>
        <span style={{ color: "#4285F4" }}>G</span>
        <span style={{ color: "#EA4335" }}>o</span>
        <span style={{ color: "#FBBC05" }}>o</span>
        <span style={{ color: "#34A853" }}>o</span>
        <span style={{ color: "#4285F4" }}>o</span>
        <span style={{ color: "#4285F4" }}>g</span>
        <span style={{ color: "#34A853" }}>l</span>
        <span style={{ color: "#EA4335" }}>e</span>
      </div>

      <div className="flex items-center gap-6 mt-4 text-sm font-medium text-[#4285F4]">
        <span className="text-gray-900 dark:text-white font-bold cursor-default">1</span>
        <button onClick={() => onPageSelect(2)} className="hover:underline">
          2
        </button>
        <button onClick={() => onPageSelect(3)} className="hover:underline">
          3
        </button>
        <button onClick={() => onPageSelect(4)} className="hover:underline">
          4
        </button>
        <button onClick={() => onPageSelect(5)} className="hover:underline">
          5
        </button>
        <button onClick={() => onPageSelect(2)} className="hover:underline flex items-center gap-1">
          Next <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
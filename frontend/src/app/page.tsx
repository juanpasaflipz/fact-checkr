'use client';

import { useEffect, useState } from 'react';
import ClaimCard from '@/components/ClaimCard';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import StatsCard from '@/components/StatsCard';
import OnboardingModal from '@/components/OnboardingModal';
import TrendingTopics from '@/components/TrendingTopics';
import QuotaWarning from '@/components/QuotaWarning';
import { getApiBaseUrl, getConnectionErrorHelp } from '@/lib/api-config';

// Define types matching the backend response
interface Claim {
  id: string;
  claim_text: string;
  original_text: string;
  verification: {
    status: "Verified" | "Debunked" | "Misleading" | "Unverified";
    explanation: string;
    sources: string[];
  } | null;
  source_post: {
    platform: string;
    author: string;
    url: string;
    timestamp: string;
  } | null;
}

export default function Home() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [activeTab, setActiveTab] = useState('todos');
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [userOnboardingStatus, setUserOnboardingStatus] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const LIMIT = 20;

  const handleRetry = () => {
    setError(null);
    setRetryCount(0);
    fetchClaims(searchQuery, false, 0, activeTab);
  };

  const fetchClaims = async (query?: string, isLoadMore = false, retryCount = 0, statusFilter?: string) => {
    setLoading(true);

    const controller = new AbortController();
    let timeoutId: NodeJS.Timeout | null = null;
    let isAborted = false;

    try {
      const baseUrl = getApiBaseUrl();
      const currentSkip = isLoadMore ? skip : 0;

      let url = '';
      if (query) {
        url = `${baseUrl}/claims/search?query=${encodeURIComponent(query)}`;
      } else {
        // Map frontend tab IDs to backend status values
        const statusMap: { [key: string]: string } = {
          'todos': '',
          'verificados': 'verified',
          'falsos': 'debunked',
          'sin-verificar': 'unverified'
        };
        const statusParam = statusFilter ? statusMap[statusFilter] || '' : (activeTab ? statusMap[activeTab] || '' : '');
        const statusQuery = statusParam ? `&status=${statusParam}` : '';
        url = `${baseUrl}/claims?skip=${currentSkip}&limit=${LIMIT}${statusQuery}`;
      }

      // Set timeout to abort request after 30 seconds
      timeoutId = setTimeout(() => {
        isAborted = true;
        if (!controller.signal.aborted) {
          controller.abort();
        }
      }, 30000);

      let response: Response;
      try {
        response = await fetch(url, {
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
          }
        });
      } catch (fetchError) {
        // Clear timeout on error
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }

        // Intercept AbortError immediately to prevent console logging
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          // Retry if we haven't exceeded limit
          if (retryCount < 2) {
            await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
            return fetchClaims(query, isLoadMore, retryCount + 1);
          }
          // Silently fail after max retries
          setLoading(false);
          return;
        }

        // Handle network errors (backend not running, CORS, etc.)
        // Check for various network error patterns
        const isNetworkError = 
          fetchError instanceof TypeError || 
          (fetchError instanceof Error && (
            fetchError.message?.includes('fetch') || 
            fetchError.message?.includes('Failed to fetch') ||
            fetchError.message?.includes('NetworkError') ||
            fetchError.message?.includes('Network request failed') ||
            fetchError.name === 'TypeError'
          )) ||
          // Handle empty error objects (common with fetch failures)
          (fetchError && typeof fetchError === 'object' && Object.keys(fetchError).length === 0);
        
        if (isNetworkError) {
          // Safely extract error message
          let errorMessage = 'Network request failed';
          if (fetchError instanceof Error) {
            errorMessage = fetchError.message || fetchError.name || 'Network error';
          } else if (typeof fetchError === 'string') {
            errorMessage = fetchError;
          } else if (fetchError && typeof fetchError === 'object') {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            errorMessage = (fetchError as any).message || JSON.stringify(fetchError) || 'Unknown network error';
          }
          
          const errorDetails = {
            url,
            baseUrl,
            errorMessage,
            errorType: fetchError instanceof Error ? fetchError.constructor.name : typeof fetchError,
            troubleshooting: getConnectionErrorHelp(),
            note: baseUrl.includes('localhost') 
              ? 'Using localhost backend. Make sure backend is running locally or set NEXT_PUBLIC_API_URL to your Railway backend URL.'
              : `Using remote backend: ${baseUrl}. Make sure this URL is correct and the backend is accessible.`
          };
          
          console.error('Network error - Backend may not be running', errorDetails);
          
          // Don't retry network errors - they're likely configuration issues
          setLoading(false);
          return;
        }

        let errorMessage = 'Unknown error';
        if (fetchError instanceof Error) {
          errorMessage = fetchError.message || fetchError.name || 'Error occurred';
        } else if (typeof fetchError === 'string') {
          errorMessage = fetchError;
        }

        // Handle other fetch errors
        setError(`Error de conexión: ${errorMessage}`);
        setLoading(false);
        return;
      }

      // Clear timeout if request completed successfully
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }

      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText);
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorJson = JSON.parse(errorText);
          if (errorJson.detail) {
            errorMessage = errorJson.detail;
          }
        } catch {
          // If not JSON, use the text as is
          if (errorText) errorMessage = errorText;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();

      if (isLoadMore) {
        setClaims(prev => [...prev, ...data]);
        setSkip(prev => prev + LIMIT);
      } else {
        setClaims(data);
        setSkip(LIMIT);
      }

      if (data.length < LIMIT) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }

    } catch (error) {
      // Clear timeout on error
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }

      // Silently handle abort errors (timeout or user cancellation)
      if (error instanceof Error && (error.name === 'AbortError' || isAborted)) {
        // Only retry if we haven't exceeded retry limit
        if (retryCount < 2) {
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
          return fetchClaims(query, isLoadMore, retryCount + 1);
        }
        // Silently fail after max retries - don't show error to user for timeouts
        return;
      }

      // Handle other errors
      // Safely extract error information
      let errorMessage = 'Unknown error';
      let errorType = 'unknown';
      
      if (error instanceof Error) {
        errorMessage = error.message || error.name || 'Error occurred';
        errorType = error.constructor.name;
      } else if (typeof error === 'string') {
        errorMessage = error;
        errorType = 'string';
      } else if (error && typeof error === 'object') {
        // Handle empty objects or objects with error info
        if (Object.keys(error).length === 0) {
          errorMessage = 'Empty error object - likely network/CORS issue';
          errorType = 'empty_object';
        } else {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          errorMessage = (error as any).message || (error as any).detail || JSON.stringify(error);
          errorType = typeof error;
        }
      } else {
        errorMessage = String(error);
        errorType = typeof error;
      }

      const isNetworkError = errorType === 'TypeError' || 
                            errorMessage.includes('Failed to fetch') ||
                            errorMessage.includes('fetch') ||
                            errorMessage.includes('NetworkError') ||
                            errorMessage.includes('Network request failed') ||
                            errorMessage.includes('network') ||
                            errorType === 'empty_object';

      if (isNetworkError) {
        const baseUrl = getApiBaseUrl();
        const currentUrl = query 
          ? `${baseUrl}/claims/search?query=${encodeURIComponent(query)}`
          : `${baseUrl}/claims?skip=${isLoadMore ? skip : 0}&limit=${LIMIT}`;
        
        // Log detailed error information
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const errorDetails: Record<string, any> = {
          url: currentUrl,
          baseUrl,
          errorMessage: errorMessage,
          errorType: errorType,
          troubleshooting: getConnectionErrorHelp()
        };
        
        // Only include error object if it has useful information
        if (error && typeof error === 'object' && Object.keys(error).length > 0) {
          errorDetails.errorObject = error;
        } else if (error) {
          errorDetails.rawError = String(error);
        }
        
        console.error('Network error - Backend may not be running:', errorDetails);
      } else {
        console.error('Error fetching claims:', error);
      }

      if (retryCount < 2 && isNetworkError) {
        console.log(`Retrying... (attempt ${retryCount + 1}/2)`);
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
        return fetchClaims(query, isLoadMore, retryCount + 1, statusFilter);
      }

      if (retryCount >= 2) {
        let errorMsg = 'No se pudieron cargar las afirmaciones.';
        const baseUrl = getApiBaseUrl();
        
        if (isNetworkError) {
          if (baseUrl.includes('localhost')) {
            errorMsg = 'No se pudo conectar con el servidor local. Verifica que el backend esté ejecutándose:\n\n' +
                       'cd backend\n' +
                       'source venv/bin/activate\n' +
                       'python main.py\n\n' +
                       `O verifica: ${baseUrl}/health`;
          } else {
            errorMsg = `No se pudo conectar con el servidor remoto: ${baseUrl}\n\n` +
                       'Verifica que el backend esté desplegado y accesible.';
          }
        } else if (error instanceof Error) {
          if (error.message.includes('Database connection timeout') || 
              error.message.includes('temporarily unavailable') ||
              error.message.includes('database_connection_error')) {
            errorMsg = 'El servicio de base de datos está temporalmente no disponible. Por favor, intenta de nuevo en unos momentos.';
          } else if (error.message.includes('Database connection error') || 
                     error.message.includes('Database error')) {
            errorMsg = 'Error de conexión a la base de datos. Por favor, intenta de nuevo más tarde.';
          } else {
            errorMsg = `Error: ${errorMessage}`;
          }
        } else {
          errorMsg = `Error desconocido: ${errorMessage}`;
        }
        
        // Only show alert if we have a meaningful error message
        if (errorMessage && errorMessage !== 'Unknown error') {
          console.error('Final error after retries:', errorMsg);
          // Set error state for UI display instead of alert
          setError(errorMsg);
          // Don't show alert for network errors in development - just log
          if (!baseUrl.includes('localhost') || process.env.NODE_ENV === 'production') {
            alert(errorMsg);
          }
        }
      }
    } finally {
      // Ensure timeout is cleared
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      setLoading(false);
    }
  };

  const [stats, setStats] = useState([
    { title: "Noticias Analizadas", value: "0", trend: "0%", trendUp: true, icon: "DocumentSearch", color: "blue" as const },
    { title: "Fake News Detectadas", value: "0", trend: "0%", trendUp: false, icon: "AlertTriangle", color: "rose" as const },
    { title: "Verificadas", value: "0", trend: "0%", trendUp: true, icon: "ShieldCheck", color: "emerald" as const },
    { title: "Fuentes Activas", value: "0", trend: "0", trendUp: true, icon: "Activity", color: "amber" as const },
  ]);

  const fetchStats = async () => {
    try {
      const baseUrl = getApiBaseUrl();
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const response = await fetch(`${baseUrl}/stats`, {
          headers: { 'Accept': 'application/json' },
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          const data = await response.json();
          const trendSign = data.trend_up ? '+' : '';
          const trendText = data.trend_percentage !== 0 ? `${trendSign}${data.trend_percentage}% vs ayer` : 'Sin cambios';
          
          setStats([
            { 
              title: "Noticias Analizadas", 
              value: data.total_analyzed.toLocaleString('es-MX'), 
              trend: trendText, 
              trendUp: data.trend_up, 
              icon: "DocumentSearch", 
              color: "blue" as const 
            },
            { 
              title: "Fake News Detectadas", 
              value: data.fake_news_detected.toLocaleString('es-MX'), 
              trend: trendText, 
              trendUp: false, 
              icon: "AlertTriangle", 
              color: "rose" as const 
            },
            { 
              title: "Verificadas", 
              value: data.verified.toLocaleString('es-MX'), 
              trend: trendText, 
              trendUp: data.trend_up, 
              icon: "ShieldCheck", 
              color: "emerald" as const 
            },
            { 
              title: "Fuentes Activas", 
              value: data.active_sources.toLocaleString('es-MX'), 
              trend: `${data.recent_24h} últimas 24h`, 
              trendUp: true, 
              icon: "Activity", 
              color: "amber" as const 
            },
          ]);
        } else {
          // Handle non-OK responses silently for stats (don't spam user)
          console.warn(`Stats endpoint returned ${response.status}`);
        }
      } catch (fetchError) {
        clearTimeout(timeoutId);
        // Silently handle abort errors (timeouts)
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          console.warn('Stats fetch timeout');
          return;
        }
        throw fetchError;
      }
    } catch (error) {
      // Silently handle stats errors - don't spam console or user
      // Stats are not critical for the app to function
      if (error instanceof Error && !error.message.includes('Failed to fetch')) {
        console.warn('Error fetching stats:', error);
      }
    }
  };

  useEffect(() => {
    fetchClaims();
    fetchStats();
    // Refresh stats every 30 seconds
    const statsInterval = setInterval(fetchStats, 30000);
    
    // Check onboarding status
    const checkOnboarding = async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      if (token) {
        try {
          const baseUrl = getApiBaseUrl();
          const response = await fetch(`${baseUrl}/api/auth/me`, {
            headers: {
              'Accept': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          });
          if (response.ok) {
            const user = await response.json();
            setUserOnboardingStatus(user.onboarding_completed);
            if (!user.onboarding_completed) {
              setShowOnboarding(true);
            }
          }
        } catch (error) {
          console.error('Error checking onboarding status:', error);
        }
      }
    };
    checkOnboarding();
    
    return () => clearInterval(statsInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Refetch claims when tab changes
  useEffect(() => {
    setSkip(0);
    setClaims([]);
    fetchClaims(undefined, false, 0, activeTab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSkip(0);
    fetchClaims(searchQuery, false, 0, activeTab);
  };

  const handleLoadMore = () => {
    fetchClaims(searchQuery, true, 0, activeTab);
  };

  const tabs = [
    { id: 'todos', label: 'Todos' },
    { id: 'verificados', label: 'Verificados' },
    { id: 'falsos', label: 'Falsos' },
    { id: 'sin-verificar', label: 'Sin verificar' },
  ];

  // Get recent claims for breaking news
  const [breakingNews, setBreakingNews] = useState<Claim[]>([]);
  const [trendingNow, setTrendingNow] = useState<Claim[]>([]);

  useEffect(() => {
    const fetchBreakingNews = async () => {
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/claims?skip=0&limit=3&status=unverified`, {
          headers: { 'Accept': 'application/json' }
        });
        if (response.ok) {
          const data = await response.json();
          setBreakingNews(data.slice(0, 3));
        }
      } catch (error) {
        console.error('Error fetching breaking news:', error);
      }
    };

    const fetchTrendingNow = async () => {
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/claims/trending?days=1&limit=5`, {
          headers: { 'Accept': 'application/json' }
        });
        if (response.ok) {
          const data = await response.json();
          setTrendingNow(data);
        }
      } catch (error) {
        // Endpoint might not exist, that's okay
      }
    };

    fetchBreakingNews();
    fetchTrendingNow();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 relative">
      {showOnboarding && (
        <OnboardingModal
          onComplete={() => {
            setShowOnboarding(false);
            setUserOnboardingStatus(true);
          }}
        />
      )}
      <Sidebar />
      <div className="lg:pl-64 relative z-10">
        <Header 
          searchQuery={searchQuery} 
          setSearchQuery={setSearchQuery} 
          onSearch={handleSearch} 
        />
        <main className="p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Quota Warning */}
            <QuotaWarning />
            
            {/* Breaking News Banner */}
            {breakingNews.length > 0 && (
              <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex items-center gap-2 bg-gray-900 border border-gray-900 px-3 py-1.5 rounded-lg">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span className="text-white font-semibold text-sm">NOTICIA DE ÚLTIMA HORA</span>
                  </div>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                    {breakingNews[0].claim_text}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {breakingNews[0].source_post?.author || 'Fuente'} • {breakingNews[0].source_post?.platform || 'Plataforma'} • Verificando ahora...
                  </p>
                </div>
              </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 animate-fade-in-up">
              {stats.map((stat, index) => (
                <div key={index} style={{ animationDelay: `${index * 100}ms` }} className="animate-fade-in-up">
                  <StatsCard {...stat} />
                </div>
              ))}
            </div>

            {/* Trending Now Section */}
            {trendingNow.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                <div className="px-6 py-5 border-b border-gray-200 bg-white">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold text-gray-900">Tendiendo Ahora</h2>
                        <p className="text-sm text-gray-600">Las afirmaciones más relevantes en este momento</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 border border-gray-200 rounded-lg">
                      <div className="w-2 h-2 bg-gray-700 rounded-full"></div>
                      <span className="text-xs font-semibold text-gray-700">EN VIVO</span>
                    </div>
                  </div>
                </div>
                <div className="divide-y divide-gray-200">
                  {trendingNow.slice(0, 3).map((claim, index) => (
                    <div key={claim.id} className="p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-gray-100 border border-gray-200 rounded-lg flex items-center justify-center text-gray-700 font-semibold text-sm">
                          {index + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-900 line-clamp-2 mb-1">{claim.claim_text}</p>
                          <div className="flex items-center gap-3 text-xs text-gray-600">
                            <span>{claim.source_post?.author || 'Desconocido'}</span>
                            <span>•</span>
                            <span>{claim.source_post?.platform || 'Unknown'}</span>
                            {claim.verification && (
                              <>
                                <span>•</span>
                                <span className={`font-semibold ${
                                  claim.verification.status === 'Verified' ? 'text-gray-900' :
                                  claim.verification.status === 'Debunked' ? 'text-gray-700' :
                                  'text-gray-600'
                                }`}>
                                  {claim.verification.status === 'Verified' ? 'Verificado' :
                                   claim.verification.status === 'Debunked' ? 'Falso' :
                                   'En verificación'}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Trending Topics Section */}
            <div className="mb-6">
              <TrendingTopics />
            </div>

            {/* Main Content Area */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
              {/* Header */}
              <div className="px-6 py-6 border-b border-gray-200 bg-white">
                <h2 className="text-gray-900 mb-5 text-xl font-semibold">
                  Feed de Verificación
                </h2>
                
                {/* Tabs with Counts */}
                <div className="relative">
                  <div 
                    className="flex gap-2 sm:gap-3 overflow-x-auto pb-1 scrollbar-hide"
                    style={{
                      scrollbarWidth: 'none',
                      msOverflowStyle: 'none',
                      WebkitOverflowScrolling: 'touch',
                      scrollSnapType: 'x mandatory'
                    }}
                    onMouseDown={(e) => {
                      // Allow scrolling but don't prevent clicks on buttons
                      const target = e.target as HTMLElement;
                      if (target.tagName !== 'BUTTON' && !target.closest('button')) {
                        // Only prevent default if clicking on the scroll container itself
                        return;
                      }
                    }}
                  >
                    {tabs.map((tab) => {
                      // Calculate counts for each tab
                      let count = 0;
                      if (tab.id === 'todos') {
                        count = stats.reduce((sum, s) => {
                          const num = parseInt(s.value.replace(/,/g, '')) || 0;
                          return sum + num;
                        }, 0);
                      } else if (tab.id === 'verificados') {
                        count = parseInt(stats.find(s => s.title === 'Verificadas')?.value.replace(/,/g, '') || '0');
                      } else if (tab.id === 'falsos') {
                        count = parseInt(stats.find(s => s.title === 'Fake News Detectadas')?.value.replace(/,/g, '') || '0');
                      } else if (tab.id === 'sin-verificar') {
                        // Estimate unverified as total - verified - fake news
                        const total = parseInt(stats.find(s => s.title === 'Noticias Analizadas')?.value.replace(/,/g, '') || '0');
                        const verified = parseInt(stats.find(s => s.title === 'Verificadas')?.value.replace(/,/g, '') || '0');
                        const fake = parseInt(stats.find(s => s.title === 'Fake News Detectadas')?.value.replace(/,/g, '') || '0');
                        count = Math.max(0, total - verified - fake);
                      }
                      
                      return (
                        <button
                          key={tab.id}
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setActiveTab(tab.id);
                          }}
                          className={`
                            relative flex-shrink-0 px-3 sm:px-5 py-2 sm:py-2.5 rounded-lg 
                            text-xs sm:text-sm transition-all duration-200 whitespace-nowrap font-semibold
                            border touch-manipulation cursor-pointer
                            ${activeTab === tab.id
                              ? 'bg-gray-900 border-gray-900 text-white'
                              : 'border-transparent text-gray-600 active:bg-gray-100 active:text-gray-900'
                            }
                            hover:bg-gray-100 hover:text-gray-900
                          `}
                          style={{
                            scrollSnapAlign: 'start',
                            minWidth: 'fit-content',
                            pointerEvents: 'auto',
                            zIndex: 10,
                          }}
                          onTouchStart={(e) => {
                            // Prevent double-tap zoom on mobile but allow clicks
                            if (e.touches.length > 1) {
                              e.preventDefault();
                            }
                            e.stopPropagation();
                          }}
                          onMouseDown={(e) => {
                            e.stopPropagation();
                          }}
                        >
                          <span className="pointer-events-none">
                            {tab.label}
                          </span>
                          {count > 0 && (
                            <span 
                              className={`
                                ml-1.5 sm:ml-2 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold pointer-events-none
                                ${activeTab === tab.id
                                  ? 'bg-white/20 text-white'
                                  : 'bg-gray-100 text-gray-600'
                                }
                              `}
                            >
                              {count > 999 ? `${(count / 1000).toFixed(1)}k` : count}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3 flex-1">
                      <h3 className="text-sm font-medium text-red-800">
                        Error al cargar datos
                      </h3>
                      <div className="mt-2 text-sm text-red-700">
                        <p>{error}</p>
                      </div>
                      <div className="mt-4">
                        <div className="-mx-2 -my-1.5 flex">
                          <button
                            onClick={handleRetry}
                            className="bg-red-50 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-red-50 focus:ring-red-600"
                          >
                            Intentar de nuevo
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Feed */}
              {loading && claims.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-gray-200 rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-gray-900 border-t-transparent rounded-full animate-spin absolute top-0"></div>
                  </div>
                  <p className="mt-8 text-gray-600 font-semibold text-lg">
                    Analizando publicaciones recientes...
                  </p>
                </div>
              ) : (
                <>
                  <div className="divide-y divide-gray-800">
                    {claims.map((claim, index) => (
                      <div key={claim.id} style={{ animationDelay: `${index * 50}ms` }} className="animate-fade-in-up">
                        <ClaimCard claim={claim} />
                      </div>
                    ))}
                  </div>

                  {claims.length === 0 && (
                    <div className="text-center py-24 px-6">
                      <div className="w-24 h-24 bg-gray-100 border-2 border-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <h3 className="text-gray-900 font-bold text-2xl mb-3">No se encontraron resultados</h3>
                      <p className="text-gray-600 font-medium mb-6 max-w-md mx-auto">
                        {activeTab === 'todos' 
                          ? 'Aún no hay afirmaciones verificadas. Nuestro sistema está analizando contenido en tiempo real.'
                          : activeTab === 'verificados'
                          ? 'No hay afirmaciones verificadas en este momento. Revisa otros filtros para ver contenido.'
                          : activeTab === 'falsos'
                          ? 'No hay afirmaciones falsas detectadas. ¡Eso es una buena señal!'
                          : 'Hay afirmaciones pendientes de verificación. Vuelve pronto para ver los resultados.'}
                      </p>
                      
                      {/* Quick Stats Preview */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
                        {stats.map((stat, index) => (
                          <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors duration-200">
                            <p className="text-xs text-gray-600 mb-1 font-medium">{stat.title}</p>
                            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                          </div>
                        ))}
                      </div>

                      <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
                        <button
                          onClick={() => setActiveTab('todos')}
                          className="px-6 py-3 bg-gray-900 text-white font-semibold rounded-lg hover:bg-gray-800 transition-colors duration-200"
                        >
                          Ver Todas las Afirmaciones
                        </button>
                        <button
                          onClick={() => {
                            setSearchQuery('');
                            fetchClaims();
                          }}
                          className="px-6 py-3 bg-white border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors duration-200"
                        >
                          Actualizar Feed
                        </button>
                      </div>
                      
                      {/* Enhanced Navigation Cards */}
                      <div className="mt-8 pt-8 border-t border-gray-200">
                        <p className="text-sm text-gray-600 mb-6 font-semibold">Explora otras secciones:</p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
                          <a href="/tendencias" className="group bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm transition-all duration-200 text-center">
                            <div className="text-3xl mb-2">📈</div>
                            <p className="text-sm font-semibold text-gray-900 group-hover:text-gray-700">Tendencias</p>
                            <p className="text-xs text-gray-600 mt-1">Análisis en tiempo real</p>
                          </a>
                          <a href="/temas" className="group bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm transition-all duration-200 text-center">
                            <div className="text-3xl mb-2">#</div>
                            <p className="text-sm font-semibold text-gray-900 group-hover:text-gray-700">Temas</p>
                            <p className="text-xs text-gray-600 mt-1">Explora por categoría</p>
                          </a>
                          <a href="/markets" className="group bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm transition-all duration-200 text-center">
                            <div className="text-3xl mb-2">💰</div>
                            <p className="text-sm font-semibold text-gray-900 group-hover:text-gray-700">Predicciones</p>
                            <p className="text-xs text-gray-600 mt-1">Predicciones colectivas</p>
                          </a>
                          <a href="/estadisticas" className="group bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm transition-all duration-200 text-center">
                            <div className="text-3xl mb-2">📊</div>
                            <p className="text-sm font-semibold text-gray-900 group-hover:text-gray-700">Estadísticas</p>
                            <p className="text-xs text-gray-600 mt-1">Métricas detalladas</p>
                          </a>
                        </div>
                      </div>
                    </div>
                  )}

                  {!loading && claims.length > 0 && hasMore && !searchQuery && (
                    <div className="px-6 py-6 text-center border-t border-gray-200 bg-white">
                      <button
                        onClick={handleLoadMore}
                        className="
                          px-10 py-3.5 
                          bg-gray-900 
                          text-white font-semibold rounded-lg 
                          hover:bg-gray-800 
                          transition-colors duration-200
                        "
                      >
                        Cargar más noticias
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

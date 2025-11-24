'use client';

import { useEffect, useState } from 'react';
import ClaimCard from '@/components/ClaimCard';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import StatsCard from '@/components/StatsCard';

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
  const LIMIT = 20;

  const fetchClaims = async (query?: string, isLoadMore = false, retryCount = 0, statusFilter?: string) => {
    setLoading(true);

    const controller = new AbortController();
    let timeoutId: NodeJS.Timeout | null = null;
    let isAborted = false;

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
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
        // Intercept AbortError immediately to prevent console logging
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          // Clear timeout and handle silently
          if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
          }
          
          // Retry if we haven't exceeded limit
          if (retryCount < 2) {
            await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
            return fetchClaims(query, isLoadMore, retryCount + 1);
          }
          // Silently fail after max retries
          setLoading(false);
          return;
        }
        // Re-throw non-abort errors
        throw fetchError;
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
      console.error('Error fetching claims:', error);

      const isNetworkError = error instanceof TypeError || 
                            (error instanceof Error && error.message.includes('Failed to fetch'));

      if (retryCount < 2 && isNetworkError) {
        console.log(`Retrying... (attempt ${retryCount + 1}/2)`);
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
        return fetchClaims(query, isLoadMore, retryCount + 1, statusFilter);
      }

      if (retryCount >= 2) {
        let errorMsg = 'No se pudieron cargar las afirmaciones.';
        if (error instanceof Error) {
          if (error.message.includes('Database connection timeout') || 
              error.message.includes('temporarily unavailable') ||
              error.message.includes('database_connection_error')) {
            errorMsg = 'El servicio de base de datos está temporalmente no disponible. Por favor, intenta de nuevo en unos momentos.';
          } else if (error.message.includes('Database connection error') || 
                     error.message.includes('Database error')) {
            errorMsg = 'Error de conexión a la base de datos. Por favor, intenta de nuevo más tarde.';
          } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg = 'No se pudo conectar con el servidor. Verifica que el backend esté ejecutándose en http://localhost:8000';
          } else {
            errorMsg = `Error: ${error.message}`;
          }
        }
        alert(errorMsg);
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
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
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
    return () => clearInterval(statsInterval);
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

  return (
    <div className="min-h-screen bg-[#F8F9FA]">
      <Sidebar />
      <div className="lg:pl-64">
        <Header 
          searchQuery={searchQuery} 
          setSearchQuery={setSearchQuery} 
          onSearch={handleSearch} 
        />
        <main className="p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-8">
            
            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
              {stats.map((stat, index) => (
                <StatsCard key={index} {...stat} />
              ))}
            </div>

            {/* Main Content Area */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              {/* Header */}
              <div className="px-6 py-5 border-b border-gray-100">
                <h2 className="text-gray-900 mb-4 text-xl font-bold">Feed de Verificación</h2>
                
                {/* Tabs */}
                <div className="flex gap-2 overflow-x-auto">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`
                        px-4 py-2 rounded-lg text-sm transition-all duration-200 whitespace-nowrap font-medium
                        ${activeTab === tab.id
                          ? 'bg-[#2563EB] text-white shadow-md shadow-[#2563EB]/20'
                          : 'text-gray-600 hover:bg-[#F8F9FA] hover:text-gray-900'
                        }
                      `}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Feed */}
              {loading && claims.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                  </div>
                  <p className="mt-6 text-gray-600 font-medium animate-pulse">Analizando publicaciones recientes...</p>
                </div>
              ) : (
                <>
                  <div className="divide-y divide-gray-100">
                    {claims.map((claim) => (
                      <ClaimCard key={claim.id} claim={claim} />
                    ))}
                  </div>

                  {claims.length === 0 && (
                    <div className="text-center py-24">
                      <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <p className="text-gray-900 font-semibold text-lg">No se encontraron resultados</p>
                      <p className="text-gray-500 mt-1">Intenta ajustar tu búsqueda o verifica los filtros.</p>
                    </div>
                  )}

                  {!loading && claims.length > 0 && hasMore && !searchQuery && (
                    <div className="px-6 py-6 text-center border-t border-gray-100">
                      <button
                        onClick={handleLoadMore}
                        className="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 hover:border-[#2563EB] hover:text-[#2563EB] transition-all duration-200 shadow-sm hover:shadow-md"
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

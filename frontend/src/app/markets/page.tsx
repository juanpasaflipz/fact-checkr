'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import { getApiBaseUrl } from '@/lib/api-config';

interface Market {
  id: number;
  slug: string;
  question: string;
  yes_probability: number;
  no_probability: number;
  volume: number;
  closes_at: string | null;
  status: string;
  claim_id: string | null;
  category: string | null;
}

const CATEGORIES = [
  { id: 'all', label: 'Todos', icon: 'Grid' },
  { id: 'politics', label: 'Política', icon: 'Users' },
  { id: 'economy', label: 'Economía', icon: 'TrendingUp' },
  { id: 'security', label: 'Seguridad', icon: 'Shield' },
  { id: 'rights', label: 'Derechos', icon: 'Scale' },
  { id: 'environment', label: 'Medio Ambiente', icon: 'Leaf' },
  { id: 'mexico-us-relations', label: 'México-EU', icon: 'Globe' },
  { id: 'institutions', label: 'Instituciones', icon: 'Building' },
] as const;

export default function MarketsPage() {
  const router = useRouter();
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const LIMIT = 20;

  const fetchMarkets = async (isLoadMore = false) => {
    setLoading(true);
    let url = '';
    try {
      const baseUrl = getApiBaseUrl();
      const currentSkip = isLoadMore ? skip : 0;
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      
      // Construct URL properly - handle empty baseUrl case
      if (baseUrl) {
        url = `${baseUrl}/api/markets?skip=${currentSkip}&limit=${LIMIT}`;
      } else {
        // For local development with Next.js proxy
        url = `/api/markets?skip=${currentSkip}&limit=${LIMIT}`;
      }
      
      if (selectedCategory === 'for_you') {
        url += '&for_you=true';
      } else if (selectedCategory !== 'all') {
        url += `&category=${selectedCategory}`;
      }

      const headers: HeadersInit = { 'Accept': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, { 
        headers,
        // Add credentials for CORS if needed
        credentials: 'omit'
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText);
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
      }

      const data: Market[] = await response.json();

      if (isLoadMore) {
        setMarkets(prev => [...prev, ...data]);
        setSkip(prev => prev + LIMIT);
      } else {
        setMarkets(data);
        setSkip(LIMIT);
      }

      setHasMore(data.length === LIMIT);
    } catch (error) {
      console.error('Error fetching markets:', error);
      // Show user-friendly error message
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('Network error - Backend may not be running or CORS issue');
        console.error('URL attempted:', url);
        console.error('Base URL:', getApiBaseUrl());
        console.error('Full error:', error);
      }
      // Don't clear markets on error, keep showing what we have
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setSkip(0);
    setMarkets([]);
    fetchMarkets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search can be implemented later with backend support
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getTimeToClose = (dateString: string | null) => {
    if (!dateString) return null;
    const now = new Date();
    const closeDate = new Date(dateString);
    const diffMs = closeDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Cerrado';
    if (diffDays === 0) return 'Cierra hoy';
    if (diffDays === 1) return 'Cierra mañana';
    if (diffDays < 7) return `Cierra en ${diffDays} días`;
    if (diffDays < 30) return `Cierra en ${Math.floor(diffDays / 7)} semanas`;
    return `Cierra en ${Math.floor(diffDays / 30)} meses`;
  };

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
            
            {/* Header - Enhanced */}
            <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-2xl shadow-xl border-2 border-blue-200/50 p-8 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl"></div>
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl">
                    <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">Mercados de Predicción</h1>
                    <p className="text-sm text-gray-600 mt-1">Inteligencia colectiva en tiempo real</p>
                  </div>
                </div>
                <p className="text-gray-700 text-base leading-relaxed max-w-3xl">
                  Plataforma de inteligencia colectiva sobre el futuro político, económico e institucional de México. 
                  Expresa tu perspectiva usando créditos virtuales y contribuye a la claridad cívica.
                </p>
                <div className="flex items-center gap-4 mt-6">
                  <div className="flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg border border-blue-200/50 shadow-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-gray-700">
                      {markets.filter(m => m.status === 'open').length} mercados activos
                    </span>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg border border-blue-200/50 shadow-sm">
                    <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm font-semibold text-gray-700">
                      {markets.reduce((sum, m) => sum + m.volume, 0).toLocaleString('es-MX')} créditos en juego
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Category Filter */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-4">
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {CATEGORIES.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`
                      px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200
                      ${selectedCategory === category.id
                        ? 'bg-[#2563EB] text-white shadow-md shadow-[#2563EB]/20'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }
                    `}
                  >
                    {category.label}
                  </button>
                ))}
                {/* "Para ti" filter - only show if user is logged in */}
                <button
                  onClick={() => {
                    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
                    if (token) {
                      setSelectedCategory('for_you');
                    } else {
                      alert('Inicia sesión para ver tu feed personalizado');
                    }
                  }}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200
                    ${selectedCategory === 'for_you'
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  ⭐ Para ti
                </button>
              </div>
            </div>

            {/* Market Insights Summary */}
            {markets.length > 0 && (
              <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-2xl p-6 border-2 border-blue-200/50 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">💡 Resumen del Mercado</h3>
                    <p className="text-sm text-gray-600">Métricas agregadas de todos los mercados</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-blue-200/50">
                    <p className="text-xs text-gray-600 mb-2 font-semibold uppercase tracking-wide">Mercados Activos</p>
                    <p className="text-3xl font-bold text-blue-600 mb-1">
                      {markets.filter(m => m.status === 'open').length}
                    </p>
                    <p className="text-xs text-gray-600">de {markets.length} totales</p>
                  </div>
                  <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-blue-200/50">
                    <p className="text-xs text-gray-600 mb-2 font-semibold uppercase tracking-wide">Volumen Total</p>
                    <p className="text-3xl font-bold text-indigo-600 mb-1">
                      {markets.reduce((sum, m) => sum + m.volume, 0).toLocaleString('es-MX')}
                    </p>
                    <p className="text-xs text-gray-600">créditos en juego</p>
                  </div>
                  <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-blue-200/50">
                    <p className="text-xs text-gray-600 mb-2 font-semibold uppercase tracking-wide">Promedio de Probabilidad</p>
                    <p className="text-3xl font-bold text-purple-600 mb-1">
                      {markets.length > 0 
                        ? ((markets.reduce((sum, m) => sum + m.yes_probability, 0) / markets.length) * 100).toFixed(1)
                        : '0'
                      }%
                    </p>
                    <p className="text-xs text-gray-600">probabilidad promedio SÍ</p>
                  </div>
                </div>
              </div>
            )}

            {/* Top Markets Leaderboard */}
            {markets.length > 0 && (
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 border-2 border-amber-200/50 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                      <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-gray-900">🏆 Mercados Destacados</h2>
                      <p className="text-sm text-gray-600">Mayor volumen y actividad</p>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {markets
                    .filter(m => m.status === 'open')
                    .sort((a, b) => b.volume - a.volume)
                    .slice(0, 3)
                    .map((market, index) => (
                      <div
                        key={market.id}
                        onClick={() => router.push(`/markets/${market.id}`)}
                        className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-amber-200/50 hover:shadow-lg transition-all duration-300 cursor-pointer hover:scale-105"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-white font-bold text-xs ${
                              index === 0 ? 'bg-gradient-to-br from-amber-500 to-yellow-500' :
                              index === 1 ? 'bg-gradient-to-br from-gray-400 to-gray-500' :
                              'bg-gradient-to-br from-orange-600 to-amber-600'
                            }`}>
                              {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                            </div>
                            <span className="text-xs font-semibold text-gray-600 uppercase">#{index + 1}</span>
                          </div>
                        </div>
                        <h3 className="font-bold text-gray-900 line-clamp-2 mb-3 text-sm">{market.question}</h3>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-600">Volumen:</span>
                            <span className="font-bold text-gray-900">{market.volume.toLocaleString('es-MX')}</span>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-green-500 to-green-600"
                              style={{ width: `${market.yes_probability * 100}%` }}
                            />
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-green-600 font-semibold">SÍ: {(market.yes_probability * 100).toFixed(0)}%</span>
                            <span className="text-red-600 font-semibold">NO: {(market.no_probability * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Markets List */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              {loading && markets.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                  </div>
                  <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando mercados...</p>
                </div>
              ) : (
                <>
                  <div className="divide-y divide-gray-100">
                    {markets.map((market) => (
                      <div
                        key={market.id}
                        onClick={() => router.push(`/markets/${market.id}`)}
                        className="p-6 hover:bg-gray-50/50 transition-colors cursor-pointer"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              {market.category && (
                                <span className="px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded border border-blue-200">
                                  {CATEGORIES.find(c => c.id === market.category)?.label || market.category}
                                </span>
                              )}
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">
                              {market.question}
                            </h3>
                            
                            {/* Visual Probability Bar */}
                            <div className="mb-4">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <span className="text-xs font-semibold text-gray-600">Probabilidad de SÍ:</span>
                                  <span className="text-lg font-bold text-green-600">
                                    {(market.yes_probability * 100).toFixed(1)}%
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs font-semibold text-gray-600">NO:</span>
                                  <span className="text-lg font-bold text-red-600">
                                    {(market.no_probability * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                                <div className="h-full flex">
                                  <div
                                    className="bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
                                    style={{ width: `${market.yes_probability * 100}%` }}
                                  />
                                  <div
                                    className="bg-gradient-to-r from-red-500 to-red-600 transition-all duration-500"
                                    style={{ width: `${market.no_probability * 100}%` }}
                                  />
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-4 sm:gap-6 flex-wrap">
                              {/* Volume */}
                              <div className="flex items-center gap-2">
                                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                                </svg>
                                <span className="text-xs font-medium text-gray-500">Volumen:</span>
                                <span className="text-sm font-semibold text-gray-900">
                                  {market.volume.toLocaleString('es-MX', { maximumFractionDigits: 0 })} créditos
                                </span>
                              </div>
                              
                              {/* Time to Close */}
                              {market.closes_at && (
                                <div className="flex items-center gap-2 text-xs">
                                  <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  <span className="text-gray-600 font-medium">{getTimeToClose(market.closes_at)}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Status Badge */}
                          <div className="flex-shrink-0">
                            <span className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold ${
                              market.status === 'open' 
                                ? 'bg-green-100 text-green-700 border border-green-200'
                                : market.status === 'resolved'
                                ? 'bg-blue-100 text-blue-700 border border-blue-200'
                                : 'bg-gray-100 text-gray-700 border border-gray-200'
                            }`}>
                              {market.status === 'open' ? 'Abierto' : market.status === 'resolved' ? 'Resuelto' : 'Cancelado'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {markets.length === 0 && (
                    <div className="text-center py-24 px-6">
                      <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <p className="text-gray-900 font-semibold text-lg mb-2">No hay mercados disponibles</p>
                      <p className="text-gray-500 mb-6 max-w-md mx-auto">
                        No se encontraron mercados de predicción activos. Los mercados se crean sobre temas relevantes 
                        del sistema político, económico e institucional de México.
                      </p>
                      <div className="flex flex-wrap items-center justify-center gap-3">
                        <button
                          onClick={() => {
                            setSelectedCategory('all');
                            fetchMarkets();
                          }}
                          className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all text-sm font-medium shadow-md"
                        >
                          Ver Todos los Mercados
                        </button>
                        <a
                          href="/"
                          className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                        >
                          Ver Feed Principal
                        </a>
                      </div>
                    </div>
                  )}

                  {!loading && markets.length > 0 && hasMore && (
                    <div className="px-6 py-6 text-center border-t border-gray-100">
                      <button
                        onClick={() => fetchMarkets(true)}
                        className="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 hover:border-[#2563EB] hover:text-[#2563EB] transition-all duration-200 shadow-sm hover:shadow-md"
                      >
                        Cargar más mercados
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


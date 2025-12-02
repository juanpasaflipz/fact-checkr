'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import ClaimCard from '@/components/ClaimCard';
import TrendingTopicsGrid from '@/components/TrendingTopicsGrid';
import TrendingEntitiesList from '@/components/TrendingEntitiesList';
import PlatformActivityChart from '@/components/PlatformActivityChart';

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

interface TrendsSummary {
  period_days: number;
  total_claims: number;
  previous_period_claims: number;
  growth_percentage: number;
  trend_up: boolean;
  status_breakdown: Array<{
    status: string;
    count: number;
  }>;
}

export default function TrendsPage() {
  const [trendingClaims, setTrendingClaims] = useState<Claim[]>([]);
  const [trendsSummary, setTrendsSummary] = useState<TrendsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [timePeriod, setTimePeriod] = useState<7 | 24 | 30>(7);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchTrendsData = async () => {
    setLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Fetch trending claims and summary in parallel
      const [claimsRes, summaryRes] = await Promise.all([
        fetch(`${baseUrl}/claims/trending?days=${timePeriod}&limit=20`),
        fetch(`${baseUrl}/trends/summary?days=${timePeriod}`)
      ]);

      if (claimsRes.ok) {
        const claimsData = await claimsRes.json();
        setTrendingClaims(claimsData);
      }

      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setTrendsSummary(summaryData);
      }
    } catch (error) {
      console.error('Error fetching trends:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrendsData();
  }, [timePeriod]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search functionality can be added later
  };

  const periodLabels = {
    7: 'Últimos 7 días',
    24: 'Últimas 24 horas',
    30: 'Últimos 30 días'
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
            
            {/* Header with Time Period Selector */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Tendencias</h1>
                <p className="text-gray-600 mt-1">Análisis de tendencias y actividad reciente</p>
              </div>
              
              <div className="flex gap-2 bg-white rounded-lg p-1 border border-gray-200 shadow-sm">
                {([7, 24, 30] as const).map((period) => (
                  <button
                    key={period}
                    onClick={() => setTimePeriod(period)}
                    className={`
                      px-4 py-2 rounded-md text-sm font-medium transition-all
                      ${timePeriod === period
                        ? 'bg-[#2563EB] text-white shadow-md'
                        : 'text-gray-600 hover:bg-gray-50'
                      }
                    `}
                  >
                    {periodLabels[period]}
                  </button>
                ))}
              </div>
            </div>

            {/* Summary Stats - Enhanced */}
            {trendsSummary && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Total de Afirmaciones</p>
                    <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-gray-900 mb-3">{trendsSummary.total_claims.toLocaleString('es-MX')}</p>
                  <div className="flex items-center gap-2 p-2 bg-white/60 rounded-lg backdrop-blur-sm">
                    {trendsSummary.trend_up ? (
                      <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                    )}
                    <span className={`text-sm font-bold ${trendsSummary.trend_up ? 'text-green-600' : 'text-red-600'}`}>
                      {trendsSummary.growth_percentage > 0 ? '+' : ''}{trendsSummary.growth_percentage}%
                    </span>
                    <span className="text-xs text-gray-600">vs período anterior</span>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl p-6 border-2 border-red-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Fake News Detectadas</p>
                    <div className="w-10 h-10 bg-red-500 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-red-600 mb-3">
                    {(
                      trendsSummary.status_breakdown
                        .filter(s => s.status === 'Debunked' || s.status === 'Misleading')
                        .reduce((sum, s) => sum + s.count, 0)
                    ).toLocaleString('es-MX')}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    <span>En este período</span>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Verificadas</p>
                    <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-green-600 mb-3">
                    {(trendsSummary.status_breakdown
                      .find(s => s.status === 'Verified')?.count || 0
                    ).toLocaleString('es-MX')}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Afirmaciones confirmadas</span>
                  </div>
                </div>
              </div>
            )}

            {/* Trending Topics Grid */}
            <TrendingTopicsGrid days={timePeriod} />

            {/* Trending Entities and Platform Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TrendingEntitiesList days={timePeriod} />
              <PlatformActivityChart days={timePeriod} />
            </div>

            {/* Viral Claims Section */}
            {trendingClaims.length > 0 && (
              <div className="bg-gradient-to-br from-purple-50 via-pink-50 to-red-50 rounded-2xl p-6 border-2 border-purple-200/50 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
                      <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">🔥 Viral Ahora</h2>
                      <p className="text-sm text-gray-600">Las afirmaciones con mayor impacto en este momento</p>
                    </div>
                  </div>
                  <div className="px-3 py-1.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg text-xs font-bold shadow-md">
                    🔥 TRENDING
                  </div>
                </div>
                <div className="space-y-3">
                  {trendingClaims.slice(0, 3).map((claim, index) => (
                    <div key={claim.id} className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-purple-200/50 hover:shadow-lg transition-all duration-300">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-md">
                          {index + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-900 line-clamp-2 mb-2">{claim.claim_text}</p>
                          <div className="flex items-center gap-3 text-xs">
                            <span className="text-gray-600">{claim.source_post?.author || 'Desconocido'}</span>
                            <span className="text-gray-400">•</span>
                            <span className="text-gray-600">{claim.source_post?.platform || 'Unknown'}</span>
                            {claim.verification && (
                              <>
                                <span className="text-gray-400">•</span>
                                <span className={`font-semibold ${
                                  claim.verification.status === 'Verified' ? 'text-green-600' :
                                  claim.verification.status === 'Debunked' ? 'text-red-600' :
                                  'text-yellow-600'
                                }`}>
                                  {claim.verification.status === 'Verified' ? '✓ Verificado' :
                                   claim.verification.status === 'Debunked' ? '✗ Falso' :
                                   '⏳ En verificación'}
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

            {/* Key Insights Section */}
            {trendsSummary && (
              <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-indigo-200/50 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">💡 Insights Clave</h2>
                    <p className="text-sm text-gray-600">Análisis del período seleccionado</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-indigo-200/50">
                    <p className="text-xs text-gray-600 mb-2 font-semibold uppercase tracking-wide">Tendencia General</p>
                    <div className="flex items-center gap-2">
                      {trendsSummary.trend_up ? (
                        <>
                          <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                          <span className="text-lg font-bold text-green-600">
                            +{trendsSummary.growth_percentage}% de crecimiento
                          </span>
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                          </svg>
                          <span className="text-lg font-bold text-red-600">
                            {trendsSummary.growth_percentage}% de disminución
                          </span>
                        </>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      Comparado con el período anterior ({trendsSummary.period_days} días)
                    </p>
                  </div>
                  <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-indigo-200/50">
                    <p className="text-xs text-gray-600 mb-2 font-semibold uppercase tracking-wide">Estado de Verificación</p>
                    <div className="space-y-2">
                      {trendsSummary.status_breakdown.map((status) => (
                        <div key={status.status} className="flex items-center justify-between">
                          <span className="text-sm text-gray-700 font-medium">{status.status}</span>
                          <span className="text-sm font-bold text-gray-900">{status.count.toLocaleString('es-MX')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Trending Claims Feed */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-white to-blue-50/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Afirmaciones en Tendencia</h2>
                    <p className="text-sm text-gray-600 mt-1">Las afirmaciones más relevantes del período seleccionado</p>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <span className="text-xs font-semibold text-blue-700">ACTUALIZANDO</span>
                  </div>
                </div>
              </div>

              {loading && trendingClaims.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                  </div>
                  <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando tendencias...</p>
                </div>
              ) : (
                <>
                  <div className="divide-y divide-gray-100">
                    {trendingClaims.map((claim, index) => (
                      <div key={claim.id} className="relative">
                        {index < 3 && (
                          <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-orange-500 to-red-500"></div>
                        )}
                        <ClaimCard claim={claim} />
                      </div>
                    ))}
                  </div>

                  {trendingClaims.length === 0 && (
                    <div className="text-center py-24 px-6">
                      <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      </div>
                      <p className="text-gray-900 font-semibold text-lg mb-2">No hay tendencias disponibles</p>
                      <p className="text-gray-500 mb-6">Intenta cambiar el período de tiempo o revisa otras secciones.</p>
                      <div className="flex flex-wrap items-center justify-center gap-3">
                        <button
                          onClick={() => setTimePeriod(7)}
                          className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                        >
                          Últimos 7 días
                        </button>
                        <button
                          onClick={() => setTimePeriod(24)}
                          className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                        >
                          Últimas 24 horas
                        </button>
                        <a
                          href="/"
                          className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all text-sm font-medium shadow-md"
                        >
                          Ver Feed Principal
                        </a>
                      </div>
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


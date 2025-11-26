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

            {/* Summary Stats */}
            {trendsSummary && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">Total de Afirmaciones</p>
                  <p className="text-3xl font-bold text-gray-900">{trendsSummary.total_claims.toLocaleString('es-MX')}</p>
                  <div className="flex items-center gap-2 mt-2">
                    {trendsSummary.trend_up ? (
                      <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                    )}
                    <span className={`text-sm font-medium ${trendsSummary.trend_up ? 'text-green-600' : 'text-red-600'}`}>
                      {trendsSummary.growth_percentage > 0 ? '+' : ''}{trendsSummary.growth_percentage}%
                    </span>
                    <span className="text-sm text-gray-500">vs período anterior</span>
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">Fake News Detectadas</p>
                  <p className="text-3xl font-bold text-red-600">
                    {(
                      trendsSummary.status_breakdown
                        .filter(s => s.status === 'Debunked' || s.status === 'Misleading')
                        .reduce((sum, s) => sum + s.count, 0)
                    ).toLocaleString('es-MX')}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">En este período</p>
                </div>

                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <p className="text-sm text-gray-600 mb-1">Verificadas</p>
                  <p className="text-3xl font-bold text-green-600">
                    {(trendsSummary.status_breakdown
                      .find(s => s.status === 'Verified')?.count || 0
                    ).toLocaleString('es-MX')}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">Afirmaciones confirmadas</p>
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

            {/* Trending Claims Feed */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-100">
                <h2 className="text-xl font-bold text-gray-900">Afirmaciones en Tendencia</h2>
                <p className="text-sm text-gray-600 mt-1">Las afirmaciones más relevantes del período seleccionado</p>
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
                    {trendingClaims.map((claim) => (
                      <ClaimCard key={claim.id} claim={claim} />
                    ))}
                  </div>

                  {trendingClaims.length === 0 && (
                    <div className="text-center py-24">
                      <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      </div>
                      <p className="text-gray-900 font-semibold text-lg">No hay tendencias disponibles</p>
                      <p className="text-gray-500 mt-1">Intenta cambiar el período de tiempo.</p>
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


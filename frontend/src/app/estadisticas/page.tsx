'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import StatsCard from '@/components/StatsCard';

interface Stats {
  total_analyzed: number;
  fake_news_detected: number;
  verified: number;
  active_sources: number;
  recent_24h: number;
  trend_percentage: number;
  trend_up: boolean;
}

interface AnalyticsData {
  period_days: number;
  daily_claims: Array<{
    date: string;
    total: number;
    verified: number;
    debunked: number;
  }>;
  platforms: Array<{
    platform: string;
    count: number;
  }>;
  status_distribution: Array<{
    status: string;
    count: number;
  }>;
}

export default function EstadisticasPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [timePeriod, setTimePeriod] = useState<7 | 30 | 90>(30);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = async () => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Fetch real-time stats and analytics in parallel
      const [statsRes, analyticsRes] = await Promise.all([
        fetch(`${baseUrl}/stats`),
        fetch(`${baseUrl}/analytics?days=${timePeriod}`)
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      } else {
        throw new Error('Failed to fetch statistics');
      }

      if (analyticsRes.ok) {
        const analyticsData = await analyticsRes.json();
        setAnalytics(analyticsData);
      }
    } catch (error) {
      console.error('Error fetching statistics:', error);
      setError('No se pudieron cargar las estadísticas. Por favor, intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, [timePeriod]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search functionality can be added later
  };

  // Calculate percentages for status distribution
  const getStatusPercentage = (count: number) => {
    if (!analytics || !analytics.status_distribution.length) return 0;
    const total = analytics.status_distribution.reduce((sum, s) => sum + s.count, 0);
    return total > 0 ? (count / total) * 100 : 0;
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', { month: 'short', day: 'numeric' });
  };

  // Get max value for chart scaling
  const getMaxDailyCount = () => {
    if (!analytics || !analytics.daily_claims.length) return 1;
    return Math.max(...analytics.daily_claims.map(d => d.total), 1);
  };

  const statusColors: Record<string, string> = {
    'Verified': 'bg-green-500',
    'Debunked': 'bg-red-500',
    'Misleading': 'bg-orange-500',
    'Unverified': 'bg-gray-400',
  };

  const statusLabels: Record<string, string> = {
    'Verified': 'Verificadas',
    'Debunked': 'Desmentidas',
    'Misleading': 'Engañosas',
    'Unverified': 'Sin Verificar',
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
                <h1 className="text-3xl font-bold text-gray-900">Estadísticas</h1>
                <p className="text-gray-600 mt-1">Análisis completo y métricas en tiempo real</p>
              </div>
              
              <div className="flex gap-2 bg-white rounded-lg p-1 border border-gray-200 shadow-sm">
                {([7, 30, 90] as const).map((period) => (
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
                    {period === 7 ? '7 días' : period === 30 ? '30 días' : '90 días'}
                  </button>
                ))}
              </div>
            </div>

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-red-800">{error}</p>
                  <button
                    onClick={fetchStatistics}
                    className="ml-auto text-sm font-medium text-red-600 hover:text-red-800 underline"
                  >
                    Reintentar
                  </button>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && !stats && (
              <div className="flex flex-col items-center justify-center py-24">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                  <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                </div>
                <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando estadísticas...</p>
              </div>
            )}

            {/* Real-time Stats Cards */}
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatsCard
                  title="Total Analizadas"
                  value={stats.total_analyzed.toLocaleString('es-MX')}
                  icon="DocumentSearch"
                  color="blue"
                  trend={stats.trend_up ? `+${stats.trend_percentage}%` : `${stats.trend_percentage}%`}
                  trendUp={stats.trend_up}
                />
                <StatsCard
                  title="Fake News Detectadas"
                  value={stats.fake_news_detected.toLocaleString('es-MX')}
                  icon="AlertTriangle"
                  color="rose"
                />
                <StatsCard
                  title="Verificadas"
                  value={stats.verified.toLocaleString('es-MX')}
                  icon="ShieldCheck"
                  color="emerald"
                />
                <StatsCard
                  title="Fuentes Activas"
                  value={stats.active_sources.toLocaleString('es-MX')}
                  icon="Activity"
                  color="amber"
                />
              </div>
            )}

            {/* Additional Stats Row */}
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-900">Últimas 24 Horas</h3>
                    <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-gray-900 mb-2">{stats.recent_24h.toLocaleString('es-MX')}</p>
                  <p className="text-sm text-gray-500">Afirmaciones analizadas hoy</p>
                </div>

                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-900">Tasa de Detección</h3>
                    <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-gray-900 mb-2">
                    {stats.total_analyzed > 0 
                      ? ((stats.fake_news_detected / stats.total_analyzed) * 100).toFixed(1)
                      : '0'
                    }%
                  </p>
                  <p className="text-sm text-gray-500">Fake news detectadas del total</p>
                </div>
              </div>
            )}

            {/* Status Distribution Chart */}
            {analytics && analytics.status_distribution.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="text-lg font-bold text-gray-900 mb-6">Distribución por Estado</h3>
                <div className="space-y-4">
                  {analytics.status_distribution.map((status) => {
                    const percentage = getStatusPercentage(status.count);
                    const color = statusColors[status.status] || statusColors['Unverified'];
                    const label = statusLabels[status.status] || status.status;
                    
                    return (
                      <div key={status.status} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`w-4 h-4 rounded-full ${color}`}></div>
                            <span className="font-medium text-gray-900">{label}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm font-bold text-gray-900">{status.count.toLocaleString('es-MX')}</span>
                            <span className="text-sm text-gray-500 w-16 text-right">{percentage.toFixed(1)}%</span>
                          </div>
                        </div>
                        <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${color}`}
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Daily Claims Chart */}
            {analytics && analytics.daily_claims.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="text-lg font-bold text-gray-900 mb-6">Tendencia Diaria de Afirmaciones</h3>
                <div className="space-y-3">
                  {analytics.daily_claims.slice(-14).map((day, index) => {
                    const maxCount = getMaxDailyCount();
                    const totalPercentage = (day.total / maxCount) * 100;
                    const verifiedPercentage = day.total > 0 ? (day.verified / day.total) * 100 : 0;
                    const debunkedPercentage = day.total > 0 ? (day.debunked / day.total) * 100 : 0;
                    
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium text-gray-700">{formatDate(day.date)}</span>
                          <span className="text-gray-500">{day.total} afirmaciones</span>
                        </div>
                        <div className="relative h-8 bg-gray-100 rounded-lg overflow-hidden">
                          <div
                            className="absolute top-0 left-0 h-full bg-green-500 transition-all duration-500"
                            style={{ width: `${(day.verified / maxCount) * 100}%` }}
                            title={`${day.verified} verificadas`}
                          ></div>
                          <div
                            className="absolute top-0 h-full bg-red-500 transition-all duration-500"
                            style={{ 
                              left: `${(day.verified / maxCount) * 100}%`,
                              width: `${(day.debunked / maxCount) * 100}%`
                            }}
                            title={`${day.debunked} desmentidas`}
                          ></div>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xs font-medium text-gray-700">{day.total}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500"></span>
                            {day.verified} verificadas
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-red-500"></span>
                            {day.debunked} desmentidas
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Platform Distribution */}
            {analytics && analytics.platforms.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="text-lg font-bold text-gray-900 mb-6">Distribución por Plataforma</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {analytics.platforms.map((platform) => {
                    const total = analytics.platforms.reduce((sum, p) => sum + p.count, 0);
                    const percentage = total > 0 ? (platform.count / total) * 100 : 0;
                    
                    return (
                      <div key={platform.platform} className="p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900">{platform.platform}</span>
                          <span className="text-sm font-bold text-gray-700">{platform.count}</span>
                        </div>
                        <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="absolute top-0 left-0 h-full bg-[#2563EB] rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}% del total</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!loading && stats && analytics && analytics.daily_claims.length === 0 && (
              <div className="bg-white rounded-2xl p-12 border border-gray-100 shadow-sm text-center">
                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <p className="text-gray-900 font-semibold text-lg">No hay datos de análisis disponibles</p>
                <p className="text-gray-500 mt-1">Los datos aparecerán aquí una vez que se analicen afirmaciones.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}


'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import SourceCard from '@/components/SourceCard';

interface Source {
  id: string;
  platform: string;
  content: string;
  author: string | null;
  url: string | null;
  timestamp: string;
  scraped_at: string;
  processed: number;
  claim_count: number;
}

interface SourceStats {
  total_sources: number;
  sources_with_claims: number;
  platforms: Array<{ platform: string; count: number }>;
  processing_status: Array<{ status: number; count: number }>;
}

type SortOption = 'recent' | 'platform' | 'claims';
type FilterStatus = 'all' | 'pending' | 'processed' | 'skipped';

export default function FuentesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('recent');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all');
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [stats, setStats] = useState<SourceStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const LIMIT = 20;

  const fetchSources = async (isLoadMore = false) => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const currentSkip = isLoadMore ? skip : 0;

      const params = new URLSearchParams({
        skip: currentSkip.toString(),
        limit: LIMIT.toString(),
      });

      if (searchQuery) {
        params.append('search', searchQuery);
      }

      if (selectedPlatform !== 'all') {
        params.append('platform', selectedPlatform);
      }

      if (filterStatus !== 'all') {
        const statusMap: { [key: string]: number } = {
          'pending': 0,
          'processed': 1,
          'skipped': 2,
        };
        params.append('processed', statusMap[filterStatus].toString());
      }

      const response = await fetch(`${baseUrl}/sources?${params.toString()}`, {
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText);
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorJson = JSON.parse(errorText);
          if (errorJson.detail) {
            errorMessage = errorJson.detail;
          }
        } catch {
          if (errorText) errorMessage = errorText;
        }
        throw new Error(errorMessage);
      }

      const data: Source[] = await response.json();

      if (isLoadMore) {
        setSources(prev => [...prev, ...data]);
        setSkip(prev => prev + LIMIT);
      } else {
        setSources(data);
        setSkip(LIMIT);
      }

      setHasMore(data.length === LIMIT);
    } catch (error) {
      console.error('Error fetching sources:', error);
      setError('No se pudieron cargar las fuentes. Por favor, intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/sources/stats`, {
        headers: { 'Accept': 'application/json' }
      });

      if (response.ok) {
        const data: SourceStats = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.warn('Error fetching source stats:', error);
    }
  };

  useEffect(() => {
    fetchSources();
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, filterStatus, selectedPlatform]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSkip(0);
    fetchSources();
  };

  const handleLoadMore = () => {
    fetchSources(true);
  };

  // Get unique platforms from stats
  const availablePlatforms = stats?.platforms.map(p => p.platform) || [];

  // Sort sources client-side (since backend already sorts by timestamp)
  const sortedSources = [...sources].sort((a, b) => {
    switch (sortBy) {
      case 'platform':
        return a.platform.localeCompare(b.platform);
      case 'claims':
        return b.claim_count - a.claim_count;
      case 'recent':
      default:
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    }
  });

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
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Header - Enhanced */}
            <div className="bg-gradient-to-br from-cyan-50 via-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-cyan-200/50 shadow-xl">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-xl">
                    <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">Fuentes</h1>
                    <p className="text-gray-600 mt-1">Explora todas las fuentes de información monitoreadas</p>
                  </div>
                </div>
                {stats && (
                  <div className="flex items-center gap-3 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg border border-cyan-200/50 shadow-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-gray-700">
                      {stats.sources_with_claims} fuentes activas
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Stats Summary - Enhanced */}
            {stats && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-6 border-2 border-blue-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Total de Fuentes</p>
                      <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center shadow-md">
                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                      </div>
                    </div>
                    <p className="text-4xl font-bold text-gray-900">{stats.total_sources.toLocaleString('es-MX')}</p>
                    <p className="text-xs text-gray-600 mt-2">Fuentes monitoreadas</p>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Con Afirmaciones</p>
                      <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center shadow-md">
                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                    </div>
                    <p className="text-4xl font-bold text-[#2563EB]">
                      {stats.sources_with_claims.toLocaleString('es-MX')}
                    </p>
                    <p className="text-xs text-gray-600 mt-2">Fuentes activas</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Plataformas</p>
                      <div className="w-10 h-10 bg-purple-500 rounded-xl flex items-center justify-center shadow-md">
                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                        </svg>
                      </div>
                    </div>
                    <p className="text-4xl font-bold text-gray-900">
                      {stats.platforms.length}
                    </p>
                    <p className="text-xs text-gray-600 mt-2">Plataformas diferentes</p>
                  </div>
                  <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 border-2 border-amber-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Pendientes</p>
                      <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center shadow-md">
                        <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                    <p className="text-4xl font-bold text-yellow-600">
                      {stats.processing_status.find(s => s.status === 0)?.count || 0}
                    </p>
                    <p className="text-xs text-gray-600 mt-2">En cola de procesamiento</p>
                  </div>
                </div>

                {/* Platform Distribution Insights */}
                {stats.platforms.length > 0 && (
                  <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-indigo-200/50 shadow-xl">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                        <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">📊 Distribución por Plataforma</h3>
                        <p className="text-sm text-gray-600">Fuentes agrupadas por plataforma de origen</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {stats.platforms
                        .sort((a, b) => b.count - a.count)
                        .slice(0, 6)
                        .map((platform) => {
                          const total = stats.platforms.reduce((sum, p) => sum + p.count, 0);
                          const percentage = total > 0 ? (platform.count / total) * 100 : 0;
                          return (
                            <div key={platform.platform} className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-indigo-200/50">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-semibold text-gray-900">{platform.platform}</span>
                                <span className="text-sm font-bold text-gray-700">{platform.count}</span>
                              </div>
                              <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <p className="text-xs text-gray-600 mt-1">{percentage.toFixed(1)}% del total</p>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Filters */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
              <div className="flex flex-col sm:flex-row gap-4">
                {/* Platform Filter */}
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Plataforma
                  </label>
                  <select
                    value={selectedPlatform}
                    onChange={(e) => {
                      setSelectedPlatform(e.target.value);
                      setSkip(0);
                    }}
                    className="w-full px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#2563EB] shadow-sm"
                  >
                    <option value="all">Todas las plataformas</option>
                    {availablePlatforms.map(platform => (
                      <option key={platform} value={platform}>
                        {platform} ({stats?.platforms.find(p => p.platform === platform)?.count || 0})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Status Filter */}
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Estado
                  </label>
                  <select
                    value={filterStatus}
                    onChange={(e) => {
                      setFilterStatus(e.target.value as FilterStatus);
                      setSkip(0);
                    }}
                    className="w-full px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#2563EB] shadow-sm"
                  >
                    <option value="all">Todos los estados</option>
                    <option value="pending">Pendiente</option>
                    <option value="processed">Procesado</option>
                    <option value="skipped">Omitido</option>
                  </select>
                </div>

                {/* Sort */}
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ordenar por
                  </label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as SortOption)}
                    className="w-full px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#2563EB] shadow-sm"
                  >
                    <option value="recent">Más recientes</option>
                    <option value="platform">Plataforma</option>
                    <option value="claims">Más afirmaciones</option>
                  </select>
                </div>
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
                    onClick={() => fetchSources()}
                    className="ml-auto text-sm font-medium text-red-600 hover:text-red-800 underline"
                  >
                    Reintentar
                  </button>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && sources.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 border border-gray-100 shadow-sm">
                <div className="flex flex-col items-center justify-center">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                  </div>
                  <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando fuentes...</p>
                </div>
              </div>
            ) : sortedSources.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 border border-gray-100 shadow-sm text-center">
                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                </div>
                <p className="text-gray-900 font-semibold text-lg mb-2">
                  {searchQuery ? 'No se encontraron fuentes' : 'No hay fuentes disponibles'}
                </p>
                <p className="text-gray-500 mb-6">
                  {searchQuery 
                    ? 'Intenta ajustar tu búsqueda o filtros.' 
                    : 'Las fuentes aparecerán aquí una vez que se agreguen al sistema.'}
                </p>
                {!searchQuery && (
                  <div className="flex flex-wrap items-center justify-center gap-3">
                    <button
                      onClick={() => {
                        setFilterStatus('all');
                        setSelectedPlatform('all');
                        setSearchQuery('');
                        fetchSources();
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-600 hover:to-blue-600 transition-all text-sm font-medium shadow-md"
                    >
                      Limpiar Filtros
                    </button>
                    <a
                      href="/"
                      className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                    >
                      Ver Feed Principal
                    </a>
                  </div>
                )}
              </div>
            ) : (
              <>
                <div className="space-y-4">
                  {sortedSources.map((source) => (
                    <SourceCard key={source.id} source={source} />
                  ))}
                </div>

                {!loading && hasMore && !searchQuery && (
                  <div className="text-center py-6">
                    <button
                      onClick={handleLoadMore}
                      className="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 hover:border-[#2563EB] hover:text-[#2563EB] transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      Cargar más fuentes
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Search Results Info */}
            {!loading && searchQuery && sortedSources.length > 0 && (
              <div className="text-center text-sm text-gray-500">
                Mostrando {sortedSources.length} fuente{sortedSources.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}


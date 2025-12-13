'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';
import TopicCard from '@/components/features/topics/TopicCard';

interface Topic {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
}

interface TopicWithStats extends Topic {
  total_claims?: number;
  verified_count?: number;
  debunked_count?: number;
  misleading_count?: number;
  unverified_count?: number;
}

type SortOption = 'name' | 'claims' | 'recent';
type ViewMode = 'grid' | 'list';

export default function TopicsPage() {
  const [topics, setTopics] = useState<TopicWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('claims');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [error, setError] = useState<string | null>(null);

  const fetchTopics = async () => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Fetch all topics
      const topicsResponse = await fetch(`${baseUrl}/topics`, {
        headers: { 'Accept': 'application/json' }
      });

      if (!topicsResponse.ok) {
        throw new Error('Failed to fetch topics');
      }

      const topicsData: Topic[] = await topicsResponse.json();

      // Fetch trending topics to get stats
      const trendingResponse = await fetch(`${baseUrl}/trends/topics?days=30&limit=100`, {
        headers: { 'Accept': 'application/json' }
      });

      let trendingData: any[] = [];
      if (trendingResponse.ok) {
        trendingData = await trendingResponse.json();
      }

      // Merge topics with stats
      const topicsWithStats: TopicWithStats[] = topicsData.map(topic => {
        const trendingInfo = trendingData.find(t => t.id === topic.id);
        return {
          ...topic,
          total_claims: trendingInfo?.claim_count || 0,
          verified_count: 0, // We'll need backend enhancement for this
          debunked_count: 0,
          misleading_count: 0,
          unverified_count: 0,
        };
      });

      setTopics(topicsWithStats);
    } catch (error) {
      console.error('Error fetching topics:', error);
      setError('No se pudieron cargar los temas. Por favor, intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search is handled by filtering in the render
  };

  const filteredAndSortedTopics = topics
    .filter(topic => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        topic.name.toLowerCase().includes(query) ||
        topic.description?.toLowerCase().includes(query) ||
        topic.slug.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'claims':
          return (b.total_claims || 0) - (a.total_claims || 0);
        case 'recent':
          // For now, sort by claims as proxy for recent activity
          return (b.total_claims || 0) - (a.total_claims || 0);
        default:
          return 0;
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
            <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-indigo-200/50 shadow-xl">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-xl">
                    <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">Temas</h1>
                    <p className="text-gray-600 mt-1">Explora y navega todos los temas de verificación</p>
                  </div>
                </div>
              
              <div className="flex items-center gap-3">
                {/* View Mode Toggle */}
                <div className="flex items-center gap-1 bg-white rounded-lg p-1 border border-gray-200 shadow-sm">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`
                      p-2 rounded-md transition-all
                      ${viewMode === 'grid'
                        ? 'bg-[#2563EB] text-white shadow-md'
                        : 'text-gray-600 hover:bg-gray-50'
                      }
                    `}
                    aria-label="Vista de cuadrícula"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`
                      p-2 rounded-md transition-all
                      ${viewMode === 'list'
                        ? 'bg-[#2563EB] text-white shadow-md'
                        : 'text-gray-600 hover:bg-gray-50'
                      }
                    `}
                    aria-label="Vista de lista"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                </div>

                {/* Sort Dropdown */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#2563EB] shadow-sm"
                >
                  <option value="claims">Más afirmaciones</option>
                  <option value="name">Alfabético</option>
                  <option value="recent">Más recientes</option>
                </select>
              </div>
              </div>
            </div>

            {/* Topic Discovery Banner - Enhanced */}
            {topics.length > 0 && (
              <div className="bg-gradient-to-r from-blue-500 via-indigo-600 to-purple-600 rounded-2xl p-6 text-white shadow-xl border-2 border-blue-400/50 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
                <div className="relative z-10">
                  <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div>
                      <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
                        <span>🔍</span>
                        <span>Descubre Temas Nuevos</span>
                      </h3>
                      <p className="text-blue-100 text-sm mb-3">
                        Explora {topics.length} temas activos con {topics.reduce((sum, t) => sum + (t.total_claims || 0), 0).toLocaleString('es-MX')} afirmaciones verificadas
                      </p>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-blue-100">
                            {topics.filter(t => (t.total_claims || 0) > 0).length} temas con actividad
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span className="text-blue-100">Actualizado en tiempo real</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg border border-white/30">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span className="font-semibold text-sm">Nuevo</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Trending Topics Quick View */}
            {topics.length > 0 && (
              <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-6 border-2 border-orange-200/50 shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">🔥 Temas Más Activos</h3>
                    <p className="text-sm text-gray-600">Los temas con mayor actividad reciente</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {topics
                    .filter(t => (t.total_claims || 0) > 0)
                    .sort((a, b) => (b.total_claims || 0) - (a.total_claims || 0))
                    .slice(0, 3)
                    .map((topic, index) => (
                      <Link
                        key={topic.id}
                        href={`/temas/${topic.slug}`}
                        className="group bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-orange-200/50 hover:border-orange-400 hover:shadow-lg transition-all duration-300"
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
                        <h4 className="font-bold text-gray-900 group-hover:text-orange-600 transition-colors mb-2 line-clamp-2">
                          {topic.name}
                        </h4>
                        <div className="flex items-center justify-between">
                          <span className="text-lg font-bold text-gray-900">
                            {(topic.total_claims || 0).toLocaleString('es-MX')}
                          </span>
                          <span className="text-xs text-gray-600">afirmaciones</span>
                        </div>
                      </Link>
                    ))}
                </div>
              </div>
            )}

            {/* Stats Summary - Enhanced */}
            {!loading && topics.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Total de Temas</p>
                    <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-gray-900">{topics.length}</p>
                  <p className="text-xs text-gray-600 mt-2">Temas monitoreados</p>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Temas Activos</p>
                    <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-[#2563EB]">
                    {topics.filter(t => (t.total_claims || 0) > 0).length}
                  </p>
                  <p className="text-xs text-gray-600 mt-2">Con afirmaciones</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Total Afirmaciones</p>
                    <div className="w-10 h-10 bg-purple-500 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-4xl font-bold text-gray-900">
                    {topics.reduce((sum, t) => sum + (t.total_claims || 0), 0).toLocaleString('es-MX')}
                  </p>
                  <p className="text-xs text-gray-600 mt-2">Afirmaciones verificadas</p>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-red-800">{error}</p>
                  <button
                    onClick={fetchTopics}
                    className="ml-auto text-sm font-medium text-red-600 hover:text-red-800 underline"
                  >
                    Reintentar
                  </button>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading ? (
              <div className="bg-white rounded-2xl p-12 border border-gray-100 shadow-sm">
                <div className="flex flex-col items-center justify-center">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                  </div>
                  <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando temas...</p>
                </div>
              </div>
            ) : filteredAndSortedTopics.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 border border-gray-100 shadow-sm text-center">
                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                  </svg>
                </div>
                <p className="text-gray-900 font-semibold text-lg mb-2">
                  {searchQuery ? 'No se encontraron temas' : 'No hay temas disponibles'}
                </p>
                <p className="text-gray-500 mb-6">
                  {searchQuery 
                    ? 'Intenta ajustar tu búsqueda.' 
                    : 'Los temas aparecerán aquí una vez que se agreguen al sistema.'}
                </p>
                {!searchQuery && (
                  <div className="flex flex-wrap items-center justify-center gap-3">
                    <a
                      href="/tendencias"
                      className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all text-sm font-medium shadow-md"
                    >
                      Ver Tendencias
                    </a>
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
              <div className={`
                ${viewMode === 'grid' 
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
                  : 'space-y-4'
                }
              `}>
                {filteredAndSortedTopics.map((topic) => (
                  <TopicCard
                    key={topic.id}
                    topic={topic}
                    stats={topic}
                    showDescription={viewMode === 'grid'}
                    variant={viewMode === 'grid' ? 'default' : 'compact'}
                  />
                ))}
              </div>
            )}

            {/* Search Results Info */}
            {!loading && searchQuery && filteredAndSortedTopics.length > 0 && (
              <div className="text-center text-sm text-gray-500">
                Mostrando {filteredAndSortedTopics.length} de {topics.length} temas
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}


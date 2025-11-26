'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import TopicCard from '@/components/TopicCard';

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
            
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Temas</h1>
                <p className="text-gray-600 mt-1">Explora y navega todos los temas de verificación</p>
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

            {/* Stats Summary */}
            {!loading && topics.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total de Temas</p>
                    <p className="text-3xl font-bold text-gray-900">{topics.length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Temas Activos</p>
                    <p className="text-3xl font-bold text-[#2563EB]">
                      {topics.filter(t => (t.total_claims || 0) > 0).length}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Afirmaciones</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {topics.reduce((sum, t) => sum + (t.total_claims || 0), 0).toLocaleString('es-MX')}
                    </p>
                  </div>
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
                <p className="text-gray-900 font-semibold text-lg">
                  {searchQuery ? 'No se encontraron temas' : 'No hay temas disponibles'}
                </p>
                <p className="text-gray-500 mt-1">
                  {searchQuery 
                    ? 'Intenta ajustar tu búsqueda.' 
                    : 'Los temas aparecerán aquí una vez que se agreguen al sistema.'}
                </p>
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


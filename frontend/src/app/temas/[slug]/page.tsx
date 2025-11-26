'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import ClaimCard from '@/components/ClaimCard';
import Link from 'next/link';

interface Topic {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
}

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

interface TopicStats {
  total_claims: number;
  verified_count: number;
  debunked_count: number;
  misleading_count: number;
  unverified_count: number;
}

export default function TopicDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [topic, setTopic] = useState<Topic | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [stats, setStats] = useState<TopicStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingClaims, setLoadingClaims] = useState(true);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'verified' | 'debunked' | 'misleading' | 'unverified'>('all');
  const LIMIT = 20;

  const fetchTopic = async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/topics`, {
        headers: { 'Accept': 'application/json' }
      });

      if (response.ok) {
        const topics: Topic[] = await response.json();
        const foundTopic = topics.find(t => t.slug === slug);
        if (foundTopic) {
          setTopic(foundTopic);
        } else {
          // Topic not found
          setTopic(null);
        }
      }
    } catch (error) {
      console.error('Error fetching topic:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/topics/${slug}/stats`, {
        headers: { 'Accept': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        setStats({
          total_claims: data.total_claims || 0,
          verified_count: data.verified_count || 0,
          debunked_count: data.debunked_count || 0,
          misleading_count: data.misleading_count || 0,
          unverified_count: data.unverified_count || 0,
        });
      }
    } catch (error) {
      console.error('Error fetching topic stats:', error);
    }
  };

  const fetchClaims = async (isLoadMore = false) => {
    setLoadingClaims(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const currentSkip = isLoadMore ? skip : 0;

      // Map frontend tab to backend status parameter
      const statusMap: { [key: string]: string } = {
        'all': '',
        'verified': 'verified',
        'debunked': 'debunked',
        'misleading': 'misleading',
        'unverified': 'unverified'
      };
      const statusParam = statusMap[activeTab] || '';
      const statusQuery = statusParam ? `&status=${statusParam}` : '';

      let url = `${baseUrl}/topics/${slug}/claims?skip=${currentSkip}&limit=${LIMIT}${statusQuery}`;
      
      const response = await fetch(url, {
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        if (response.status === 404) {
          setClaims([]);
          setHasMore(false);
          return;
        }
        throw new Error('Failed to fetch claims');
      }

      const data: Claim[] = await response.json();

      if (isLoadMore) {
        setClaims(prev => [...prev, ...data]);
        setSkip(prev => prev + LIMIT);
      } else {
        setClaims(data);
        setSkip(LIMIT);
      }

      setHasMore(data.length === LIMIT);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoadingClaims(false);
    }
  };

  useEffect(() => {
    if (slug) {
      fetchTopic();
    }
  }, [slug]);

  useEffect(() => {
    if (topic) {
      fetchStats();
      setSkip(0);
      setClaims([]);
      fetchClaims(false);
    }
  }, [topic, activeTab]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search functionality can be enhanced later
  };

  const handleLoadMore = () => {
    fetchClaims(true);
  };

  const filteredClaims = claims.filter(claim => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      claim.claim_text.toLowerCase().includes(query) ||
      claim.original_text.toLowerCase().includes(query) ||
      claim.verification?.explanation.toLowerCase().includes(query)
    );
  });

  const tabs = [
    { id: 'all' as const, label: 'Todos', count: stats?.total_claims || 0 },
    { id: 'verified' as const, label: 'Verificados', count: stats?.verified_count || 0 },
    { id: 'debunked' as const, label: 'Falsos', count: stats?.debunked_count || 0 },
    { id: 'misleading' as const, label: 'Engañosos', count: stats?.misleading_count || 0 },
    { id: 'unverified' as const, label: 'Sin verificar', count: stats?.unverified_count || 0 },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA]">
        <Sidebar />
        <div className="lg:pl-64">
          <Header searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSearch={handleSearch} />
          <main className="p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
              <div className="flex flex-col items-center justify-center py-24">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                  <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                </div>
                <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando tema...</p>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="min-h-screen bg-[#F8F9FA]">
        <Sidebar />
        <div className="lg:pl-64">
          <Header searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSearch={handleSearch} />
          <main className="p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
              <div className="bg-white rounded-2xl p-12 border border-gray-100 shadow-sm text-center">
                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-gray-900 font-semibold text-lg mb-2">Tema no encontrado</p>
                <p className="text-gray-500 mb-6">El tema que buscas no existe o ha sido eliminado.</p>
                <Link
                  href="/temas"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#2563EB] text-white rounded-lg hover:bg-[#1e40af] transition-colors font-medium"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Volver a Temas
                </Link>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

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
            
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-sm text-gray-600">
              <Link href="/temas" className="hover:text-[#2563EB] transition-colors">
                Temas
              </Link>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-gray-900 font-medium">{topic.name}</span>
            </nav>

            {/* Topic Header */}
            <div className="bg-white rounded-2xl p-8 border border-gray-100 shadow-sm">
              <div className="flex items-start justify-between gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="size-14 rounded-xl bg-linear-to-br from-[#2563EB] to-[#1e40af] flex items-center justify-center">
                      <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                      </svg>
                    </div>
                    <div>
                      <h1 className="text-3xl font-bold text-gray-900">{topic.name}</h1>
                      {topic.description && (
                        <p className="text-gray-600 mt-2">{topic.description}</p>
                      )}
                    </div>
                  </div>

                  {/* Stats Grid */}
                  {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Total</p>
                        <p className="text-2xl font-bold text-gray-900">{stats.total_claims}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Verificadas</p>
                        <p className="text-2xl font-bold text-green-600">{stats.verified_count}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Falsas</p>
                        <p className="text-2xl font-bold text-red-600">{stats.debunked_count}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Engañosas</p>
                        <p className="text-2xl font-bold text-yellow-600">{stats.misleading_count}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Claims Section */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-100">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Afirmaciones</h2>
                
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
                      {tab.label} {tab.count > 0 && `(${tab.count})`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Claims Feed */}
              {loadingClaims && claims.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                  </div>
                  <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando afirmaciones...</p>
                </div>
              ) : (
                <>
                  <div className="divide-y divide-gray-100">
                    {filteredClaims.map((claim) => (
                      <ClaimCard key={claim.id} claim={claim} />
                    ))}
                  </div>

                  {filteredClaims.length === 0 && (
                    <div className="text-center py-24">
                      <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <p className="text-gray-900 font-semibold text-lg">
                        {searchQuery ? 'No se encontraron afirmaciones' : 'No hay afirmaciones disponibles'}
                      </p>
                      <p className="text-gray-500 mt-1">
                        {searchQuery 
                          ? 'Intenta ajustar tu búsqueda.' 
                          : 'Las afirmaciones aparecerán aquí una vez que se agreguen a este tema.'}
                      </p>
                    </div>
                  )}

                  {!loadingClaims && filteredClaims.length > 0 && hasMore && !searchQuery && (
                    <div className="px-6 py-6 text-center border-t border-gray-100">
                      <button
                        onClick={handleLoadMore}
                        className="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 hover:border-[#2563EB] hover:text-[#2563EB] transition-all duration-200 shadow-sm hover:shadow-md"
                      >
                        Cargar más afirmaciones
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


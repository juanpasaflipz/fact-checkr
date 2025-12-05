'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import MarketAnalytics from '@/components/MarketAnalytics';
import { getApiBaseUrl } from '@/lib/api-config';

interface MarketAnalyticsData {
  market_id: number;
  history: Array<{
    timestamp: string;
    yes_probability: number;
    no_probability: number;
    volume: number;
  }>;
  category_trends?: {
    category: string;
    total_markets: number;
    total_volume: number;
    average_probability: number;
    resolved_markets: number;
  };
  current_probability: {
    yes: number;
    no: number;
  };
}

export default function MarketAnalyticsPage() {
  const params = useParams();
  const router = useRouter();
  const marketId = params.id as string;
  
  const [analytics, setAnalytics] = useState<MarketAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [days, setDays] = useState(30);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const baseUrl = getApiBaseUrl();
        const token = localStorage.getItem('token');
        
        if (!token) {
          router.push('/');
          return;
        }

        const response = await fetch(
          `${baseUrl}/api/markets/${marketId}/analytics?days=${days}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        );

        if (response.status === 403) {
          setError('Esta función requiere una suscripción Pro. Actualiza tu plan para acceder a análisis avanzados.');
          return;
        }

        if (!response.ok) {
          throw new Error('Error al cargar análisis');
        }

        const data = await response.json();
        setAnalytics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };

    if (marketId) {
      fetchAnalytics();
    }
  }, [marketId, days, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Sidebar />
        <div className="ml-64 p-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Cargando análisis...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Sidebar />
        <div className="ml-64 p-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error</h2>
            <p className="text-red-600">{error}</p>
            {error.includes('Pro') && (
              <button
                onClick={() => router.push('/subscription')}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Actualizar a Pro
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="ml-64 p-8">
        <Header 
          searchQuery={searchQuery} 
          setSearchQuery={setSearchQuery}
          onSearch={() => {}}
        />
        
        <div className="mt-8">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Análisis del Mercado</h1>
            <div className="flex items-center gap-4">
              <label className="text-sm text-gray-600">
                Período:
                <select
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="ml-2 px-3 py-1 border border-gray-300 rounded"
                >
                  <option value={7}>7 días</option>
                  <option value={30}>30 días</option>
                  <option value={90}>90 días</option>
                  <option value={365}>1 año</option>
                </select>
              </label>
              <button
                onClick={() => router.push(`/markets/${marketId}`)}
                className="px-4 py-2 text-gray-600 hover:text-gray-900"
              >
                ← Volver al Mercado
              </button>
            </div>
          </div>

          <MarketAnalytics
            history={analytics.history}
            currentProbability={analytics.current_probability}
            categoryTrends={analytics.category_trends}
          />
        </div>
      </div>
    </div>
  );
}


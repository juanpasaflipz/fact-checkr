'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';
import Leaderboard from '@/components/Leaderboard';
import { getApiBaseUrl } from '@/lib/api-config';

interface LeaderboardEntry {
  rank: number;
  username: string;
  accuracy_rate: number;
  total_trades: number;
  total_volume: number;
  credits_earned: number;
}

export default function LeaderboardPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState<'accuracy' | 'volume' | 'trades'>('accuracy');
  const [category, setCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchLeaderboard();
  }, [metric, category]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const baseUrl = getApiBaseUrl();
      
      const params = new URLSearchParams({
        metric,
        limit: '100',
      });
      
      if (category) {
        params.append('category', category);
      }

      const response = await fetch(`${baseUrl}/api/markets/leaderboard?${params.toString()}`);

      if (!response.ok) {
        throw new Error('Error al cargar clasificación');
      }

      const data = await response.json();
      setEntries(data);
    } catch (err) {
      console.error('Error fetching leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };

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
            <h1 className="text-2xl font-bold text-gray-900">Clasificación de Mercados</h1>
            <div className="flex items-center gap-4">
              <label className="text-sm text-gray-600">
                Ordenar por:
                <select
                  value={metric}
                  onChange={(e) => setMetric(e.target.value as 'accuracy' | 'volume' | 'trades')}
                  className="ml-2 px-3 py-1 border border-gray-300 rounded"
                >
                  <option value="accuracy">Precisión</option>
                  <option value="volume">Volumen</option>
                  <option value="trades">Operaciones</option>
                </select>
              </label>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Cargando clasificación...</p>
            </div>
          ) : (
            <Leaderboard entries={entries} metric={metric} />
          )}

          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">¿Cómo funciona la clasificación?</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li><strong>Precisión:</strong> Porcentaje de operaciones ganadoras</li>
              <li><strong>Volumen:</strong> Total de créditos operados</li>
              <li><strong>Operaciones:</strong> Número total de operaciones realizadas</li>
              <li>La clasificación se actualiza cuando los mercados se resuelven</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}


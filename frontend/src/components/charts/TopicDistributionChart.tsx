'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface TopicData {
  topic_id: number;
  topic_name: string;
  topic_slug: string;
  claim_count: number;
  verified_count: number;
  debunked_count: number;
  misleading_count: number;
  unverified_count: number;
  percentage: number;
}

interface TopicDistributionResponse {
  topics: TopicData[];
  total_claims: number;
  period_days: number;
}

const COLORS = ['#00f0ff', '#ff00ff', '#00ff88', '#ff6b00', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444'];

export default function TopicDistributionChart({ days = 30 }: { days?: number }) {
  const [data, setData] = useState<TopicDistributionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'count' | 'status'>('count');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/analytics/topics/distribution?days=${days}&limit=10`);
        if (response.ok) {
          const result = await response.json();
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching topic distribution:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [days]);

  if (loading) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <div className="h-64 bg-[#1a1a24] rounded-lg animate-pulse"></div>
      </div>
    );
  }

  if (!data || data.topics.length === 0) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <h3 className="text-xl font-bold text-[#00f0ff] mb-4"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
          Distribución por Temas
        </h3>
        <p className="text-gray-400 text-center py-12">No hay datos disponibles</p>
      </div>
    );
  }

  // Prepare data for pie chart
  const pieData = data.topics.map((topic, index) => ({
    name: topic.topic_name,
    value: viewMode === 'count' ? topic.claim_count : topic.percentage,
    fullData: topic,
    color: COLORS[index % COLORS.length]
  }));

  // Status breakdown data
  const statusData = data.topics.slice(0, 5).map((topic, index) => ({
    name: topic.topic_name,
    verified: topic.verified_count,
    debunked: topic.debunked_count,
    misleading: topic.misleading_count,
    unverified: topic.unverified_count,
    color: COLORS[index % COLORS.length]
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload.fullData;
      return (
        <div className="bg-[#1a1a24] border-2 border-[#00f0ff]/50 rounded-lg p-4"
             style={{ boxShadow: '0 0 20px rgba(0, 240, 255, 0.4)' }}>
          <p className="font-bold text-[#00f0ff] mb-2">{data.topic_name}</p>
          <p className="text-sm text-gray-300">Total: {data.claim_count.toLocaleString()}</p>
          <div className="mt-2 space-y-1 text-xs">
            <p className="text-[#00ff88]">✓ Verificadas: {data.verified_count}</p>
            <p className="text-[#ff00ff]">✗ Falsas: {data.debunked_count}</p>
            <p className="text-[#ff6b00]">⚠ Engañosas: {data.misleading_count}</p>
            <p className="text-gray-400">⏳ Sin verificar: {data.unverified_count}</p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
         style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-[#00f0ff]"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
          Distribución por Temas
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('count')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              viewMode === 'count'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Cantidad
          </button>
          <button
            onClick={() => setViewMode('status')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              viewMode === 'status'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Porcentaje
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value, percent }) => 
                  `${name}: ${viewMode === 'count' ? value.toLocaleString() : `${(percent * 100).toFixed(1)}%`}`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Status Breakdown */}
        <div className="space-y-4">
          <h4 className="text-lg font-bold text-[#00f0ff]">Desglose por Estado</h4>
          {statusData.map((topic) => {
            const total = topic.verified + topic.debunked + topic.misleading + topic.unverified;
            return (
              <div key={topic.name} className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-gray-200">{topic.name}</span>
                  <span className="text-sm text-gray-400">{total} total</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#00ff88]"></div>
                    <span className="text-xs text-gray-300">Verificadas: {topic.verified}</span>
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#00ff88]"
                        style={{ width: `${(topic.verified / total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#ff00ff]"></div>
                    <span className="text-xs text-gray-300">Falsas: {topic.debunked}</span>
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#ff00ff]"
                        style={{ width: `${(topic.debunked / total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#ff6b00]"></div>
                    <span className="text-xs text-gray-300">Engañosas: {topic.misleading}</span>
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#ff6b00]"
                        style={{ width: `${(topic.misleading / total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                    <span className="text-xs text-gray-300">Sin verificar: {topic.unverified}</span>
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gray-500"
                        style={{ width: `${(topic.unverified / total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-400 text-center">
        Total: {data.total_claims.toLocaleString()} afirmaciones en los últimos {data.period_days} días
      </div>
    </div>
  );
}


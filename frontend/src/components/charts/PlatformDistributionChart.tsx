'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface PlatformData {
  platform: string;
  total_count: number;
  verified_count: number;
  debunked_count: number;
  misleading_count: number;
  unverified_count: number;
  percentage: number;
  avg_engagement?: number;
}

interface PlatformDistributionResponse {
  platforms: PlatformData[];
  total_sources: number;
  period_days: number;
}

const PLATFORM_COLORS: Record<string, string> = {
  'Twitter': '#1DA1F2',
  'Reddit': '#FF4500',
  'Google News': '#4285F4',
  'Facebook': '#1877F2',
  'Instagram': '#E4405F',
  'YouTube': '#FF0000',
  'default': '#6B7280'
};

export default function PlatformDistributionChart({ days = 30 }: { days?: number }) {
  const [data, setData] = useState<PlatformDistributionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartType, setChartType] = useState<'bar' | 'pie'>('bar');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/analytics/platforms/distribution?days=${days}`);
        if (response.ok) {
          const result = await response.json();
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching platform distribution:', error);
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

  if (!data || data.platforms.length === 0) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <h3 className="text-xl font-bold text-[#00f0ff] mb-4"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
          Distribución por Plataforma
        </h3>
        <p className="text-gray-400 text-center py-12">No hay datos disponibles</p>
      </div>
    );
  }

  const chartData = data.platforms.map(platform => ({
    name: platform.platform,
    Total: platform.total_count,
    Verificadas: platform.verified_count,
    Falsas: platform.debunked_count,
    Engañosas: platform.misleading_count,
    'Sin verificar': platform.unverified_count,
    percentage: platform.percentage,
    avg_engagement: platform.avg_engagement || 0,
    color: PLATFORM_COLORS[platform.platform] || PLATFORM_COLORS.default
  }));

  const pieData = data.platforms.map(platform => ({
    name: platform.platform,
    value: platform.total_count,
    color: PLATFORM_COLORS[platform.platform] || PLATFORM_COLORS.default
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1a1a24] border-2 border-[#00f0ff]/50 rounded-lg p-4"
             style={{ boxShadow: '0 0 20px rgba(0, 240, 255, 0.4)' }}>
          <p className="font-bold text-[#00f0ff] mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toLocaleString()}
            </p>
          ))}
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
          Distribución por Plataforma
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setChartType('bar')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              chartType === 'bar'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Barras
          </button>
          <button
            onClick={() => setChartType('pie')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              chartType === 'pie'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Circular
          </button>
        </div>
      </div>

      {chartType === 'bar' ? (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="name" 
              stroke="#00f0ff"
              tick={{ fill: '#00f0ff' }}
            />
            <YAxis 
              stroke="#00f0ff"
              tick={{ fill: '#00f0ff' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="Verificadas" fill="#00ff88" />
            <Bar dataKey="Falsas" fill="#ff00ff" />
            <Bar dataKey="Engañosas" fill="#ff6b00" />
            <Bar dataKey="Sin verificar" fill="#6b7280" />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
              outerRadius={120}
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
      )}

      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        {data.platforms.slice(0, 4).map((platform) => (
          <div 
            key={platform.platform}
            className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20"
          >
            <div className="flex items-center gap-2 mb-2">
              <div 
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: PLATFORM_COLORS[platform.platform] || PLATFORM_COLORS.default }}
              ></div>
              <span className="font-semibold text-gray-200">{platform.platform}</span>
            </div>
            <p className="text-2xl font-bold text-[#00f0ff]">{platform.total_count.toLocaleString()}</p>
            <p className="text-xs text-gray-400 mt-1">
              {platform.percentage.toFixed(1)}% del total
            </p>
            {platform.avg_engagement && (
              <p className="text-xs text-[#00ff88] mt-1">
                Engagement: {platform.avg_engagement.toFixed(0)}
              </p>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 text-sm text-gray-400 text-center">
        Total: {data.total_sources.toLocaleString()} fuentes en los últimos {data.period_days} días
      </div>
    </div>
  );
}


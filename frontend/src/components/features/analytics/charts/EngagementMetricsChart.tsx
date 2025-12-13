'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface EngagementMetric {
  platform: string;
  total_likes: number;
  total_retweets: number;
  total_replies: number;
  total_views: number;
  avg_likes: number;
  avg_retweets: number;
  avg_replies: number;
  avg_views: number;
  post_count: number;
}

interface EngagementResponse {
  metrics: EngagementMetric[];
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

export default function EngagementMetricsChart({ days = 30 }: { days?: number }) {
  const [data, setData] = useState<EngagementResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'total' | 'average'>('total');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/analytics/engagement/metrics?days=${days}`);
        if (response.ok) {
          const result = await response.json();
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching engagement metrics:', error);
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

  if (!data || data.metrics.length === 0) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <h3 className="text-xl font-bold text-[#00f0ff] mb-4"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
          Métricas de Engagement
        </h3>
        <p className="text-gray-400 text-center py-12">No hay datos de engagement disponibles</p>
      </div>
    );
  }

  const chartData = data.metrics.map(metric => ({
    name: metric.platform,
    Likes: viewMode === 'total' ? metric.total_likes : metric.avg_likes,
    Retweets: viewMode === 'total' ? metric.total_retweets : metric.avg_retweets,
    Replies: viewMode === 'total' ? metric.total_replies : metric.avg_replies,
    Views: viewMode === 'total' ? metric.total_views : metric.avg_views,
    color: PLATFORM_COLORS[metric.platform] || PLATFORM_COLORS.default
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const metric = data.metrics.find(m => m.platform === label);
      return (
        <div className="bg-[#1a1a24] border-2 border-[#00f0ff]/50 rounded-lg p-4"
             style={{ boxShadow: '0 0 20px rgba(0, 240, 255, 0.4)' }}>
          <p className="font-bold text-[#00f0ff] mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toLocaleString()}
            </p>
          ))}
          {metric && (
            <div className="mt-2 pt-2 border-t border-gray-700">
              <p className="text-xs text-gray-400">Posts: {metric.post_count}</p>
            </div>
          )}
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
          Métricas de Engagement
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('total')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              viewMode === 'total'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Totales
          </button>
          <button
            onClick={() => setViewMode('average')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              viewMode === 'average'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Promedio
          </button>
        </div>
      </div>

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
          <Bar dataKey="Likes" fill="#00f0ff" />
          <Bar dataKey="Retweets" fill="#ff00ff" />
          <Bar dataKey="Replies" fill="#00ff88" />
          <Bar dataKey="Views" fill="#8b5cf6" />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.metrics.slice(0, 3).map((metric) => {
          const totalEngagement = metric.total_likes + metric.total_retweets + metric.total_replies;
          return (
            <div 
              key={metric.platform}
              className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20"
            >
              <div className="flex items-center gap-2 mb-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: PLATFORM_COLORS[metric.platform] || PLATFORM_COLORS.default }}
                ></div>
                <span className="font-semibold text-gray-200">{metric.platform}</span>
              </div>
              <div className="space-y-2">
                <div>
                  <p className="text-xs text-gray-400">Total Engagement</p>
                  <p className="text-2xl font-bold text-[#00f0ff]">{totalEngagement.toLocaleString()}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-gray-400">Likes</p>
                    <p className="text-[#00f0ff]">{metric.total_likes.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Retweets</p>
                    <p className="text-[#ff00ff]">{metric.total_retweets.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Replies</p>
                    <p className="text-[#00ff88]">{metric.total_replies.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Posts</p>
                    <p className="text-gray-300">{metric.post_count}</p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 text-sm text-gray-400 text-center">
        Período: últimos {data.period_days} días
      </div>
    </div>
  );
}


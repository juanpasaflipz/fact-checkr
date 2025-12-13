'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
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

interface AuthorData {
  author: string;
  post_count: number;
  total_engagement: number;
  avg_engagement: number;
}

interface AudienceStats {
  total_sources: number;
  unique_authors: number;
  platforms: PlatformData[];
  engagement_metrics: EngagementMetric[];
  top_authors: AuthorData[];
}

interface AudienceStatsResponse {
  total_sources: number;
  unique_authors: number;
  platforms: PlatformData[];
  engagement_metrics: EngagementMetric[];
  top_authors: AuthorData[];
}

export default function AudienceStatsChart({ days = 30 }: { days?: number }) {
  const [data, setData] = useState<AudienceStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/analytics/audience/stats?days=${days}&limit=10`);
        if (response.ok) {
          const result = await response.json();
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching audience stats:', error);
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

  if (!data) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <p className="text-gray-400 text-center py-12">No hay datos disponibles</p>
      </div>
    );
  }

  const authorChartData = data.top_authors.slice(0, 10).map(author => ({
    name: author.author.length > 15 ? author.author.substring(0, 15) + '...' : author.author,
    fullName: author.author,
    'Posts': author.post_count,
    'Engagement': author.total_engagement,
    'Promedio': author.avg_engagement
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#1a1a24] border-2 border-[#00f0ff]/50 rounded-lg p-4"
             style={{ boxShadow: '0 0 20px rgba(0, 240, 255, 0.4)' }}>
          <p className="font-bold text-[#00f0ff] mb-2">{data.fullName}</p>
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
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <h3 className="text-xl font-bold text-[#00f0ff] mb-6"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
          Estadísticas de Audiencia
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20">
            <p className="text-sm text-gray-400 mb-2">Total de Fuentes</p>
            <p className="text-3xl font-bold text-[#00f0ff]">{data.total_sources.toLocaleString()}</p>
          </div>
          <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#00ff88]/20">
            <p className="text-sm text-gray-400 mb-2">Autores Únicos</p>
            <p className="text-3xl font-bold text-[#00ff88]">{data.unique_authors.toLocaleString()}</p>
          </div>
          <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#ff00ff]/20">
            <p className="text-sm text-gray-400 mb-2">Plataformas Activas</p>
            <p className="text-3xl font-bold text-[#ff00ff]">{data.platforms.length}</p>
          </div>
        </div>
      </div>

      {/* Top Authors Chart */}
      {data.top_authors.length > 0 && (
        <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
             style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
          <h3 className="text-xl font-bold text-[#00f0ff] mb-6"
              style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
            Top Autores por Engagement
          </h3>
          
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={authorChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis 
                dataKey="name" 
                stroke="#00f0ff"
                tick={{ fill: '#00f0ff', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis 
                stroke="#00f0ff"
                tick={{ fill: '#00f0ff' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="Posts" fill="#00f0ff" />
              <Bar dataKey="Engagement" fill="#ff00ff" />
              <Bar dataKey="Promedio" fill="#00ff88" />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.top_authors.slice(0, 6).map((author, index) => (
              <div 
                key={author.author}
                className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 bg-[#00f0ff] rounded-full flex items-center justify-center text-[#0a0a0f] font-bold">
                    {index + 1}
                  </div>
                  <span className="font-semibold text-gray-200 truncate">{author.author}</span>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Posts:</span>
                    <span className="text-[#00f0ff] font-semibold">{author.post_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Engagement:</span>
                    <span className="text-[#ff00ff] font-semibold">{author.total_engagement.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Promedio:</span>
                    <span className="text-[#00ff88] font-semibold">{author.avg_engagement.toFixed(0)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Platform Engagement Summary */}
      {data.engagement_metrics.length > 0 && (
        <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
             style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
          <h3 className="text-xl font-bold text-[#00f0ff] mb-6"
              style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
            Resumen de Engagement por Plataforma
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.engagement_metrics.map((metric) => {
              const totalEngagement = metric.total_likes + metric.total_retweets + metric.total_replies;
              return (
                <div 
                  key={metric.platform}
                  className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20"
                >
                  <h4 className="font-bold text-[#00f0ff] mb-3">{metric.platform}</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <p className="text-xs text-gray-400">Total Engagement</p>
                      <p className="text-xl font-bold text-[#00f0ff]">{totalEngagement.toLocaleString()}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      <div>
                        <p className="text-xs text-gray-400">Likes</p>
                        <p className="text-[#00f0ff]">{metric.total_likes.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400">Retweets</p>
                        <p className="text-[#ff00ff]">{metric.total_retweets.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400">Replies</p>
                        <p className="text-[#00ff88]">{metric.total_replies.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400">Views</p>
                        <p className="text-gray-300">{metric.total_views.toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="mt-2 pt-2 border-t border-gray-700">
                      <p className="text-xs text-gray-400">Posts analizados: {metric.post_count}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}


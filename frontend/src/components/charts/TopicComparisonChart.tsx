'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface TopicComparison {
  topic_id: number;
  topic_name: string;
  topic_slug: string;
  total_claims: number;
  verification_rate: number;
  debunk_rate: number;
  avg_confidence: number;
  engagement_score: number;
  trend_score?: number;
}

interface TopicComparisonResponse {
  topics: TopicComparison[];
  period_days: number;
}

export default function TopicComparisonChart({ topicIds, days = 30 }: { topicIds: number[], days?: number }) {
  const [data, setData] = useState<TopicComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartType, setChartType] = useState<'bar' | 'radar'>('bar');

  useEffect(() => {
    if (topicIds.length === 0) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const baseUrl = getApiBaseUrl();
        const ids = topicIds.join(',');
        const response = await fetch(`${baseUrl}/api/analytics/topics/compare?topic_ids=${ids}&days=${days}`);
        if (response.ok) {
          const result = await response.json();
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching topic comparison:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [topicIds, days]);

  if (topicIds.length === 0) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <p className="text-gray-400 text-center py-12">Selecciona temas para comparar</p>
      </div>
    );
  }

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
        <p className="text-gray-400 text-center py-12">No hay datos disponibles para comparar</p>
      </div>
    );
  }

  const barData = data.topics.map(topic => ({
    name: topic.topic_name,
    'Tasa Verificación': topic.verification_rate,
    'Tasa Falsas': topic.debunk_rate,
    'Confianza Promedio': topic.avg_confidence * 100,
    'Engagement': topic.engagement_score / 1000, // Normalize for display
    'Tendencia': topic.trend_score ? topic.trend_score * 100 : 0
  }));

  // Create radar data structure: array of metrics, each with values for all topics
  const radarData = [
    {
      subject: 'Verificación',
      ...data.topics.reduce((acc, topic, index) => {
        acc[topic.topic_name] = topic.verification_rate;
        return acc;
      }, {} as Record<string, number>)
    },
    {
      subject: 'Falsas',
      ...data.topics.reduce((acc, topic, index) => {
        acc[topic.topic_name] = topic.debunk_rate;
        return acc;
      }, {} as Record<string, number>)
    },
    {
      subject: 'Confianza',
      ...data.topics.reduce((acc, topic, index) => {
        acc[topic.topic_name] = topic.avg_confidence * 100;
        return acc;
      }, {} as Record<string, number>)
    },
    {
      subject: 'Engagement',
      ...data.topics.reduce((acc, topic, index) => {
        acc[topic.topic_name] = Math.min(topic.engagement_score / 100, 100);
        return acc;
      }, {} as Record<string, number>)
    },
    {
      subject: 'Tendencia',
      ...data.topics.reduce((acc, topic, index) => {
        acc[topic.topic_name] = topic.trend_score ? topic.trend_score * 100 : 0;
        return acc;
      }, {} as Record<string, number>)
    }
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1a1a24] border-2 border-[#00f0ff]/50 rounded-lg p-4"
             style={{ boxShadow: '0 0 20px rgba(0, 240, 255, 0.4)' }}>
          <p className="font-bold text-[#00f0ff] mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(2)}
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
          Comparación de Temas
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
            onClick={() => setChartType('radar')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              chartType === 'radar'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Radar
          </button>
        </div>
      </div>

      {chartType === 'bar' ? (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={barData}>
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
            <Bar dataKey="Tasa Verificación" fill="#00ff88" />
            <Bar dataKey="Tasa Falsas" fill="#ff00ff" />
            <Bar dataKey="Confianza Promedio" fill="#00f0ff" />
            <Bar dataKey="Engagement" fill="#8b5cf6" />
            <Bar dataKey="Tendencia" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#333" />
            <PolarAngleAxis dataKey="subject" stroke="#00f0ff" tick={{ fill: '#00f0ff' }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#00f0ff" tick={{ fill: '#00f0ff' }} />
            {data.topics.map((topic, index) => {
              const colors = ['#00f0ff', '#ff00ff', '#00ff88', '#8b5cf6', '#f59e0b'];
              return (
                <Radar
                  key={topic.topic_id}
                  name={topic.topic_name}
                  dataKey={topic.topic_name}
                  stroke={colors[index % colors.length]}
                  fill={colors[index % colors.length]}
                  fillOpacity={0.3}
                />
              );
            })}
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      )}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.topics.map((topic) => (
          <div 
            key={topic.topic_id}
            className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20"
          >
            <h4 className="font-bold text-[#00f0ff] mb-3">{topic.topic_name}</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Total Claims:</span>
                <span className="text-gray-200 font-semibold">{topic.total_claims}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Tasa Verificación:</span>
                <span className="text-[#00ff88] font-semibold">{topic.verification_rate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Tasa Falsas:</span>
                <span className="text-[#ff00ff] font-semibold">{topic.debunk_rate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Confianza Promedio:</span>
                <span className="text-[#00f0ff] font-semibold">{(topic.avg_confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Engagement:</span>
                <span className="text-[#8b5cf6] font-semibold">{topic.engagement_score.toFixed(0)}</span>
              </div>
              {topic.trend_score && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Tendencia:</span>
                  <span className="text-[#f59e0b] font-semibold">{(topic.trend_score * 100).toFixed(1)}%</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


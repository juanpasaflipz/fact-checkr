'use client';

import { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface TrendingTopic {
  id: number;
  topic_name: string;
  topic_keywords: string[];
  trend_score: number;
  engagement_velocity: number;
  cross_platform_correlation: number;
  context_relevance_score: number;
  misinformation_risk_score: number;
  final_priority_score: number;
  detected_at: string;
  topic_metadata?: any;
}

export default function TrendingTopics() {
  const [topics, setTopics] = useState<TrendingTopic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTrendingTopics();
  }, []);

  const fetchTrendingTopics = async () => {
    try {
      setLoading(true);
      setError(null);
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/v1/trending/topics?limit=10`, {
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // No trending topics yet - not an error
          setTopics([]);
          setLoading(false);
          return;
        }
        throw new Error(`Failed to fetch trending topics: ${response.statusText}`);
      }

      const data = await response.json();
      setTopics(data.topics || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching trending topics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2), inset 0 0 30px rgba(0, 240, 255, 0.05)' }}>
        <h2 className="text-xl font-bold mb-4 text-[#00f0ff]"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>Temas en Tendencia</h2>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-[#1a1a24] rounded border border-[#00f0ff]/20"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2), inset 0 0 30px rgba(0, 240, 255, 0.05)' }}>
        <h2 className="text-xl font-bold mb-4 text-[#00f0ff]"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>Temas en Tendencia</h2>
        <p className="text-red-400 text-sm mb-2">Error: {error}</p>
        <button
          onClick={fetchTrendingTopics}
          className="mt-2 text-sm text-[#00f0ff] hover:text-[#00ffff] underline transition"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
         style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2), inset 0 0 30px rgba(0, 240, 255, 0.05)' }}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-[#00f0ff]"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>Temas en Tendencia</h2>
        <button
          onClick={fetchTrendingTopics}
          className="text-sm text-[#00f0ff] hover:text-[#00ffff] transition"
          title="Actualizar temas en tendencia"
        >
          🔄 Actualizar
        </button>
      </div>

      {topics.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-400">No hay temas en tendencia en este momento.</p>
          <p className="text-sm text-gray-500 mt-2">
            Los temas en tendencia se detectan automáticamente cada 2 horas.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {topics.map((topic) => (
            <div
              key={topic.id}
              className="border-2 border-[#00f0ff]/20 rounded-lg p-4 hover:bg-[#1a1a24] hover:border-[#00f0ff]/40 transition cursor-pointer bg-[#0a0a0f]"
              onClick={() => {
                // Could navigate to topic detail page
                console.log('Topic clicked:', topic.id);
              }}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-lg text-gray-200">{topic.topic_name}</h3>
                <div className="flex items-center space-x-2">
                  <span className="text-xs bg-[#1a1a24] border border-[#00f0ff]/50 text-[#00f0ff] px-2 py-1 rounded font-medium"
                        style={{ boxShadow: '0 0 10px rgba(0, 240, 255, 0.3)' }}>
                    Prioridad: {(topic.final_priority_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mb-3">
                {topic.topic_keywords.slice(0, 5).map((keyword, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-[#1a1a24] border border-[#00f0ff]/30 text-gray-300 px-2 py-1 rounded"
                  >
                    {keyword}
                  </span>
                ))}
                {topic.topic_keywords.length > 5 && (
                  <span className="text-xs text-gray-500 px-2 py-1">
                    +{topic.topic_keywords.length - 5} más
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Tendencia:</span>
                  <span className="ml-2 font-medium text-gray-200">
                    {(topic.trend_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Velocidad:</span>
                  <span className="ml-2 font-medium text-gray-200">
                    {topic.engagement_velocity?.toFixed(1) || '0.0'}/hora
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Relevancia:</span>
                  <span className="ml-2 font-medium text-gray-200">
                    {topic.context_relevance_score 
                      ? (topic.context_relevance_score * 100).toFixed(0) + '%'
                      : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Riesgo:</span>
                  <span className={`ml-2 font-medium ${
                    topic.misinformation_risk_score && topic.misinformation_risk_score > 0.6 ? 'text-red-400' :
                    topic.misinformation_risk_score && topic.misinformation_risk_score > 0.3 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {topic.misinformation_risk_score 
                      ? (topic.misinformation_risk_score * 100).toFixed(0) + '%'
                      : 'N/A'}
                  </span>
                </div>
              </div>

              <div className="mt-3 text-xs text-gray-500">
                Detectado: {new Date(topic.detected_at).toLocaleString('es-MX', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


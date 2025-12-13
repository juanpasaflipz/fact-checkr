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
      const url = `${baseUrl}/api/v1/trending/topics?limit=10`;
      console.log('Fetching trending topics from:', url);
      
      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // No trending topics yet - not an error
          console.log('No trending topics endpoint found, returning empty list');
          setTopics([]);
          setLoading(false);
          return;
        }
        const errorText = await response.text();
        console.error('Failed to fetch trending topics:', response.status, errorText);
        throw new Error(`Failed to fetch trending topics: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log('Trending topics response:', data);
      setTopics(data.topics || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Error fetching trending topics:', err);
      // Set empty topics on error to prevent UI breaking
      setTopics([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Temas en Tendencia</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-50 rounded border border-gray-200 animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Temas en Tendencia</h2>
        <p className="text-sm text-gray-600 mb-3">Error: {error}</p>
        <button
          onClick={fetchTrendingTopics}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Temas en Tendencia</h2>
        <button
          onClick={fetchTrendingTopics}
          className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
          title="Actualizar temas en tendencia"
        >
          Actualizar
        </button>
      </div>

      {topics.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600">No hay temas en tendencia en este momento.</p>
          <p className="text-sm text-gray-500 mt-2">
            Los temas en tendencia se detectan automáticamente cada 2 horas.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {topics.map((topic) => (
            <div
              key={topic.id}
              className="border border-gray-200 rounded-lg p-5 hover:border-gray-300 hover:shadow-sm transition-all cursor-pointer bg-white"
              onClick={() => {
                // Could navigate to topic detail page
                console.log('Topic clicked:', topic.id);
              }}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-base text-gray-900">{topic.topic_name}</h3>
                <span className="text-xs bg-gray-100 border border-gray-200 text-gray-700 px-2.5 py-1 rounded font-medium">
                  Prioridad: {(topic.final_priority_score * 100).toFixed(0)}%
                </span>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                {topic.topic_keywords.slice(0, 5).map((keyword, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-gray-50 border border-gray-200 text-gray-700 px-2.5 py-1 rounded font-medium"
                  >
                    {keyword}
                  </span>
                ))}
                {topic.topic_keywords.length > 5 && (
                  <span className="text-xs text-gray-500 px-2.5 py-1">
                    +{topic.topic_keywords.length - 5} más
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Tendencia:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {(topic.trend_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Velocidad:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {topic.engagement_velocity?.toFixed(1) || '0.0'}/hora
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Relevancia:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {topic.context_relevance_score 
                      ? (topic.context_relevance_score * 100).toFixed(0) + '%'
                      : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Riesgo:</span>
                  <span className={`ml-2 font-semibold ${
                    topic.misinformation_risk_score && topic.misinformation_risk_score > 0.6 ? 'text-red-700' :
                    topic.misinformation_risk_score && topic.misinformation_risk_score > 0.3 ? 'text-amber-700' :
                    'text-gray-900'
                  }`}>
                    {topic.misinformation_risk_score 
                      ? (topic.misinformation_risk_score * 100).toFixed(0) + '%'
                      : 'N/A'}
                  </span>
                </div>
              </div>

              <div className="mt-4 text-xs text-gray-500 border-t border-gray-100 pt-3">
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


'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface TrendingTopic {
  id: number;
  name: string;
  slug: string;
  claim_count: number;
  previous_count: number;
  growth_percentage: number;
  trend_up: boolean;
}

interface TrendingTopicsGridProps {
  days: number;
}

export default function TrendingTopicsGrid({ days }: TrendingTopicsGridProps) {
  const [topics, setTopics] = useState<TrendingTopic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTopics = async () => {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/trends/topics?days=${days}&limit=8`);
        
        if (response.ok) {
          const data = await response.json();
          setTopics(data);
        }
      } catch (error) {
        console.error('Error fetching trending topics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTopics();
  }, [days]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Temas en Tendencia</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">Temas en Tendencia</h3>
        <span className="text-sm text-gray-500">{topics.length} temas activos</span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {topics.map((topic) => (
          <Link
            key={topic.id}
            href={`/temas/${topic.slug}`}
            className="group p-4 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200 hover:border-[#2563EB] hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-semibold text-gray-900 group-hover:text-[#2563EB] transition-colors line-clamp-2">
                {topic.name}
              </h4>
            </div>
            
            <div className="flex items-center justify-between mt-3">
              <div>
                <p className="text-2xl font-bold text-gray-900">{topic.claim_count}</p>
                <p className="text-xs text-gray-500">afirmaciones</p>
              </div>
              
              {topic.growth_percentage !== 0 && (
                <div className="flex items-center gap-1">
                  {topic.trend_up ? (
                    <>
                      <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      <span className="text-sm font-semibold text-green-600">
                        +{topic.growth_percentage}%
                      </span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      <span className="text-sm font-semibold text-red-600">
                        {topic.growth_percentage}%
                      </span>
                    </>
                  )}
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>

      {topics.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No hay temas en tendencia en este período</p>
        </div>
      )}
    </div>
  );
}


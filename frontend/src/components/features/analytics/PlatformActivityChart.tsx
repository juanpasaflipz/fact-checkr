'use client';

import { useEffect, useState } from 'react';

interface PlatformData {
  platform: string;
  total_count: number;
  debunked_count: number;
  verified_count: number;
}

interface DailyData {
  date: string;
  count: number;
}

interface PlatformActivityData {
  platforms: PlatformData[];
  daily_breakdown: Record<string, DailyData[]>;
}

interface PlatformActivityChartProps {
  days: number;
}

const platformColors: Record<string, string> = {
  'Twitter': '#1DA1F2',
  'Reddit': '#FF4500',
  'Google News': '#4285F4',
  'Facebook': '#1877F2',
  'Instagram': '#E4405F',
  'YouTube': '#FF0000',
  'default': '#6B7280'
};

export default function PlatformActivityChart({ days }: PlatformActivityChartProps) {
  const [data, setData] = useState<PlatformActivityData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlatformData = async () => {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/trends/platforms?days=${days}`);
        
        if (response.ok) {
          const responseData = await response.json();
          setData(responseData);
        }
      } catch (error) {
        console.error('Error fetching platform activity:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlatformData();
  }, [days]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Actividad por Plataforma</h3>
        <div className="h-64 bg-gray-100 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  if (!data || data.platforms.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Actividad por Plataforma</h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No hay datos de plataformas disponibles</p>
        </div>
      </div>
    );
  }

  const maxCount = Math.max(...data.platforms.map(p => p.total_count), 1);

  return (
    <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">Actividad por Plataforma</h3>
        <span className="text-sm text-gray-500">{data.platforms.length} plataformas</span>
      </div>
      
      <div className="space-y-4">
        {data.platforms.slice(0, 6).map((platform) => {
          const percentage = (platform.total_count / maxCount) * 100;
          const color = platformColors[platform.platform] || platformColors.default;
          
          return (
            <div key={platform.platform} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: color }}
                  ></div>
                  <span className="font-medium text-gray-900">{platform.platform}</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-sm font-bold text-gray-900">{platform.total_count}</span>
                    <span className="text-xs text-gray-500 ml-1">total</span>
                  </div>
                </div>
              </div>
              
              <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ 
                    width: `${percentage}%`,
                    backgroundColor: color,
                    opacity: 0.8
                  }}
                ></div>
              </div>
              
              <div className="flex items-center gap-4 text-xs text-gray-600">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  {platform.verified_count} verificadas
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-500"></span>
                  {platform.debunked_count} falsas
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {data.platforms.length > 6 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-500 text-center">
            Y {data.platforms.length - 6} plataforma{data.platforms.length - 6 > 1 ? 's' : ''} más
          </p>
        </div>
      )}
    </div>
  );
}


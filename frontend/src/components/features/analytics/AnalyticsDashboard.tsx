'use client';

import { useEffect, useState } from 'react';

interface AnalyticsData {
  period_days: number;
  daily_claims: Array<{
    date: string;
    total: number;
    verified: number;
    debunked: number;
  }>;
  platforms: Array<{
    platform: string;
    count: number;
  }>;
  status_distribution: Array<{
    status: string;
    count: number;
  }>;
}

export default function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/analytics?days=30`);
        if (response.ok) {
          const data = await response.json();
          setAnalytics(data);
        }
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <p className="text-gray-500">Cargando análisis...</p>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Distribución por Estado</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {analytics.status_distribution.map((stat) => (
            <div key={stat.status} className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{stat.count}</p>
              <p className="text-sm text-gray-500">{stat.status}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Plataformas</h3>
        <div className="space-y-2">
          {analytics.platforms.map((platform) => (
            <div key={platform.platform} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="font-medium text-gray-900">{platform.platform}</span>
              <span className="text-gray-600">{platform.count} noticias</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


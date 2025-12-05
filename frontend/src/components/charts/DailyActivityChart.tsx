'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';
import { format, parseISO } from 'date-fns';

interface DailyActivity {
  date: string;
  claims_count: number;
  verified_count: number;
  debunked_count: number;
  misleading_count: number;
  unverified_count: number;
}

interface DailyActivityResponse {
  daily_activity: DailyActivity[];
  period_days: number;
}

export default function DailyActivityChart({ days = 30 }: { days?: number }) {
  const [data, setData] = useState<DailyActivityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'line' | 'area'>('line');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/analytics/daily/activity?days=${days}`);
        if (response.ok) {
          const result = await response.json();
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching daily activity:', error);
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

  if (!data || data.daily_activity.length === 0) {
    return (
      <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
           style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
        <h3 className="text-xl font-bold text-[#00f0ff] mb-4"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
          Actividad Diaria
        </h3>
        <p className="text-gray-400 text-center py-12">No hay datos disponibles</p>
      </div>
    );
  }

  const chartData = data.daily_activity.map(day => ({
    date: format(parseISO(day.date), 'dd/MM'),
    fullDate: day.date,
    Total: day.claims_count,
    Verificadas: day.verified_count,
    Falsas: day.debunked_count,
    Engañosas: day.misleading_count,
    'Sin verificar': day.unverified_count
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
          Actividad Diaria
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('line')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              viewMode === 'line'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Líneas
          </button>
          <button
            onClick={() => setViewMode('area')}
            className={`px-3 py-1 rounded-lg text-sm font-bold transition-all ${
              viewMode === 'area'
                ? 'bg-[#00f0ff] text-[#0a0a0f]'
                : 'bg-[#1a1a24] text-gray-400 border border-gray-700'
            }`}
          >
            Área
          </button>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        {viewMode === 'line' ? (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="date" 
              stroke="#00f0ff"
              tick={{ fill: '#00f0ff' }}
            />
            <YAxis 
              stroke="#00f0ff"
              tick={{ fill: '#00f0ff' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line type="monotone" dataKey="Total" stroke="#00f0ff" strokeWidth={2} />
            <Line type="monotone" dataKey="Verificadas" stroke="#00ff88" strokeWidth={2} />
            <Line type="monotone" dataKey="Falsas" stroke="#ff00ff" strokeWidth={2} />
            <Line type="monotone" dataKey="Engañosas" stroke="#ff6b00" strokeWidth={2} />
            <Line type="monotone" dataKey="Sin verificar" stroke="#6b7280" strokeWidth={2} />
          </LineChart>
        ) : (
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="date" 
              stroke="#00f0ff"
              tick={{ fill: '#00f0ff' }}
            />
            <YAxis 
              stroke="#00f0ff"
              tick={{ fill: '#00f0ff' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area type="monotone" dataKey="Verificadas" stackId="1" stroke="#00ff88" fill="#00ff88" fillOpacity={0.6} />
            <Area type="monotone" dataKey="Falsas" stackId="1" stroke="#ff00ff" fill="#ff00ff" fillOpacity={0.6} />
            <Area type="monotone" dataKey="Engañosas" stackId="1" stroke="#ff6b00" fill="#ff6b00" fillOpacity={0.6} />
            <Area type="monotone" dataKey="Sin verificar" stackId="1" stroke="#6b7280" fill="#6b7280" fillOpacity={0.6} />
          </AreaChart>
        )}
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20">
          <p className="text-xs text-gray-400 mb-1">Total</p>
          <p className="text-2xl font-bold text-[#00f0ff]">
            {data.daily_activity.reduce((sum, day) => sum + day.claims_count, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#00ff88]/20">
          <p className="text-xs text-gray-400 mb-1">Verificadas</p>
          <p className="text-2xl font-bold text-[#00ff88]">
            {data.daily_activity.reduce((sum, day) => sum + day.verified_count, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#ff00ff]/20">
          <p className="text-xs text-gray-400 mb-1">Falsas</p>
          <p className="text-2xl font-bold text-[#ff00ff]">
            {data.daily_activity.reduce((sum, day) => sum + day.debunked_count, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#ff6b00]/20">
          <p className="text-xs text-gray-400 mb-1">Engañosas</p>
          <p className="text-2xl font-bold text-[#ff6b00]">
            {data.daily_activity.reduce((sum, day) => sum + day.misleading_count, 0).toLocaleString()}
          </p>
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-400 text-center">
        Período: últimos {data.period_days} días
      </div>
    </div>
  );
}


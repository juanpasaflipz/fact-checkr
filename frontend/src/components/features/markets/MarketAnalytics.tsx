'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

interface HistoryPoint {
  timestamp: string;
  yes_probability: number;
  no_probability: number;
  volume: number;
}

interface MarketAnalyticsProps {
  history: HistoryPoint[];
  currentProbability: {
    yes: number;
    no: number;
  };
  categoryTrends?: {
    category: string;
    total_markets: number;
    total_volume: number;
    average_probability: number;
    resolved_markets: number;
  };
}

export default function MarketAnalytics({ history, currentProbability, categoryTrends }: MarketAnalyticsProps) {
  // Format data for charts
  const chartData = history.map((point) => ({
    ...point,
    timestamp: format(new Date(point.timestamp), 'MMM dd, HH:mm'),
    yesPercent: (point.yes_probability * 100).toFixed(1),
    noPercent: (point.no_probability * 100).toFixed(1),
  }));

  return (
    <div className="space-y-6">
      {/* Probability History Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Historial de Probabilidades</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              domain={[0, 100]}
              label={{ value: 'Probabilidad (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value: number) => `${value}%`}
              labelFormatter={(label) => `Fecha: ${label}`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="yesPercent" 
              stroke="#10b981" 
              strokeWidth={2}
              name="SÍ (%)"
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="noPercent" 
              stroke="#ef4444" 
              strokeWidth={2}
              name="NO (%)"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Volume Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Volumen de Operaciones</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              label={{ value: 'Volumen (créditos)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value: number) => `${value.toFixed(2)} créditos`}
              labelFormatter={(label) => `Fecha: ${label}`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="volume" 
              stroke="#3b82f6" 
              strokeWidth={2}
              name="Volumen Total"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Current Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Probabilidades Actuales</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-green-700">SÍ</span>
                <span className="text-sm font-semibold text-green-700">
                  {(currentProbability.yes * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-green-600 h-2.5 rounded-full" 
                  style={{ width: `${currentProbability.yes * 100}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-red-700">NO</span>
                <span className="text-sm font-semibold text-red-700">
                  {(currentProbability.no * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-red-600 h-2.5 rounded-full" 
                  style={{ width: `${currentProbability.no * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {categoryTrends && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Tendencias de Categoría</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Categoría:</span>
                <span className="font-medium">{categoryTrends.category}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Mercados Totales:</span>
                <span className="font-medium">{categoryTrends.total_markets}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Volumen Total:</span>
                <span className="font-medium">{categoryTrends.total_volume.toFixed(2)} créditos</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Probabilidad Promedio:</span>
                <span className="font-medium">{(categoryTrends.average_probability * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Mercados Resueltos:</span>
                <span className="font-medium">{categoryTrends.resolved_markets}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


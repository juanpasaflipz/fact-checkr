'use client';

import { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface CalibrationBucket {
  range: string;
  predicted_avg: number;
  actual_frequency: number;
  count: number;
  calibration_error: number;
}

interface CalibrationData {
  agent_id: string;
  brier_score: number;
  calibration_error: number;
  num_predictions: number;
  num_resolved: number;
  overconfidence_bias: number;
  time_period_days: number;
  buckets: CalibrationBucket[];
}

interface CalibrationDashboardProps {
  agentId?: string;
  className?: string;
}

export default function CalibrationDashboard({ 
  agentId = 'synthesizer_v1',
  className = '' 
}: CalibrationDashboardProps) {
  const [data, setData] = useState<CalibrationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCalibration = async () => {
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(
          `${baseUrl}/api/markets/calibration/${agentId}?days=90`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch calibration data');
        }
        
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error fetching data');
      } finally {
        setLoading(false);
      }
    };

    fetchCalibration();
  }, [agentId]);

  if (loading) {
    return (
      <div className={`bg-white rounded-xl shadow-lg p-6 animate-pulse ${className}`}>
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-48 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`bg-white rounded-xl shadow-lg p-6 ${className}`}>
        <p className="text-gray-500 text-center">
          {error || 'No hay datos de calibración disponibles'}
        </p>
      </div>
    );
  }

  // Determine Brier score quality
  const brierQuality = 
    data.brier_score < 0.15 ? 'Excelente' :
    data.brier_score < 0.20 ? 'Bueno' :
    data.brier_score < 0.25 ? 'Aceptable' :
    'Necesita mejora';

  const brierColor =
    data.brier_score < 0.15 ? 'text-green-600' :
    data.brier_score < 0.20 ? 'text-blue-600' :
    data.brier_score < 0.25 ? 'text-yellow-600' :
    'text-red-600';

  return (
    <div className={`bg-white rounded-xl shadow-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Precisión del Agente de IA
        </h3>
        <p className="text-emerald-100 text-sm mt-1">
          Calibración basada en {data.num_resolved} predicciones resueltas
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Brier Score */}
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className={`text-2xl font-bold ${brierColor}`}>
              {data.brier_score.toFixed(3)}
            </div>
            <div className="text-xs text-gray-500 mt-1">Brier Score</div>
            <div className={`text-xs font-semibold ${brierColor} mt-1`}>
              {brierQuality}
            </div>
          </div>

          {/* Calibration Error */}
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {(data.calibration_error * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Error de Calibración</div>
          </div>

          {/* Predictions */}
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {data.num_predictions}
            </div>
            <div className="text-xs text-gray-500 mt-1">Predicciones</div>
          </div>

          {/* Overconfidence */}
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className={`text-2xl font-bold ${
              data.overconfidence_bias > 0.05 ? 'text-orange-600' :
              data.overconfidence_bias < -0.05 ? 'text-blue-600' :
              'text-green-600'
            }`}>
              {data.overconfidence_bias > 0 ? '+' : ''}{(data.overconfidence_bias * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {data.overconfidence_bias > 0.05 ? 'Sobreconfianza' :
               data.overconfidence_bias < -0.05 ? 'Subconfianza' :
               'Bien calibrado'}
            </div>
          </div>
        </div>

        {/* Calibration Curve */}
        {data.buckets.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              Curva de Calibración
            </h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="relative h-48">
                {/* Perfect calibration line */}
                <div 
                  className="absolute bottom-0 left-0 w-full border-b-2 border-dashed border-gray-300"
                  style={{ height: '100%' }}
                >
                  <div 
                    className="absolute w-0.5 h-full bg-gray-300 opacity-50"
                    style={{ 
                      transform: 'rotate(-45deg)', 
                      transformOrigin: 'bottom left',
                      width: '141%'
                    }}
                  />
                </div>

                {/* Calibration points */}
                <div className="absolute inset-0 flex items-end justify-around">
                  {data.buckets.map((bucket, idx) => {
                    const predictedHeight = bucket.predicted_avg * 100;
                    const actualHeight = bucket.actual_frequency * 100;
                    
                    return (
                      <div key={idx} className="relative flex flex-col items-center w-12">
                        {/* Predicted bar */}
                        <div 
                          className="w-4 bg-blue-400 rounded-t opacity-50"
                          style={{ height: `${predictedHeight}%` }}
                          title={`Predicho: ${(bucket.predicted_avg * 100).toFixed(0)}%`}
                        />
                        {/* Actual bar */}
                        <div 
                          className="w-4 bg-green-500 rounded-t absolute bottom-0"
                          style={{ height: `${actualHeight}%` }}
                          title={`Actual: ${(bucket.actual_frequency * 100).toFixed(0)}%`}
                        />
                        {/* Label */}
                        <div className="text-xs text-gray-500 mt-1 absolute -bottom-5">
                          {bucket.range}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Legend */}
              <div className="flex justify-center gap-6 mt-8 pt-4 border-t">
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 bg-blue-400 rounded opacity-50"></div>
                  <span className="text-gray-600">Predicho</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 bg-green-500 rounded"></div>
                  <span className="text-gray-600">Resultado Real</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-8 border-b-2 border-dashed border-gray-400"></div>
                  <span className="text-gray-600">Calibración Perfecta</span>
                </div>
              </div>
            </div>

            <p className="text-xs text-gray-500 mt-2">
              Una IA bien calibrada tiene barras verdes (resultados reales) que coinciden 
              con las barras azules (predicciones). Si dice 70%, debería acertar ~70% de las veces.
            </p>
          </div>
        )}

        {/* Bucket Details */}
        {data.buckets.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              Detalle por Rango
            </h4>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2 font-medium text-gray-600">Rango</th>
                    <th className="text-right py-2 px-2 font-medium text-gray-600">Predicho</th>
                    <th className="text-right py-2 px-2 font-medium text-gray-600">Real</th>
                    <th className="text-right py-2 px-2 font-medium text-gray-600">Error</th>
                    <th className="text-right py-2 px-2 font-medium text-gray-600">N</th>
                  </tr>
                </thead>
                <tbody>
                  {data.buckets.map((bucket, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-2 font-medium">{bucket.range}</td>
                      <td className="py-2 px-2 text-right text-blue-600">
                        {(bucket.predicted_avg * 100).toFixed(0)}%
                      </td>
                      <td className="py-2 px-2 text-right text-green-600">
                        {(bucket.actual_frequency * 100).toFixed(0)}%
                      </td>
                      <td className={`py-2 px-2 text-right ${
                        bucket.calibration_error > 0.1 ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {(bucket.calibration_error * 100).toFixed(1)}%
                      </td>
                      <td className="py-2 px-2 text-right text-gray-500">
                        {bucket.count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Interpretation */}
        <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
          <h4 className="text-sm font-semibold text-indigo-800 mb-2">
            ¿Qué significa esto?
          </h4>
          <div className="text-sm text-indigo-700 space-y-1">
            <p>
              <strong>Brier Score:</strong> Mide el error cuadrático medio de las predicciones. 
              Menor es mejor. &lt;0.15 es excelente, &lt;0.25 es aceptable.
            </p>
            <p>
              <strong>Calibración:</strong> Una IA calibrada acierta en la proporción que predice. 
              Si dice "70% SÍ", debería acertar ~70% de las veces.
            </p>
            <p>
              <strong>Sobreconfianza:</strong> Valores positivos indican que la IA es demasiado 
              extrema en sus predicciones.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

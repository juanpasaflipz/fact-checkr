'use client';

import { useState } from 'react';

interface KeyFactor {
  factor: string;
  impact: number;
  confidence: number;
  source: string;
  evidence?: string;
}

interface RiskFactor {
  risk: string;
  severity: string;
  probability: number;
  impact_on_prediction: string;
}

interface PredictionData {
  raw_probability: number;
  calibrated_probability: number;
  confidence: number;
  probability_low: number;
  probability_high: number;
  key_factors: KeyFactor[];
  risk_factors: RiskFactor[];
  reasoning_chain?: string;
  summary?: string;
  data_freshness_hours: number;
  analysis_tier: number;
}

interface PredictionExplanationProps {
  prediction: PredictionData | null;
  loading?: boolean;
}

export default function PredictionExplanation({ prediction, loading }: PredictionExplanationProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-200 animate-pulse">
        <div className="h-6 bg-indigo-200 rounded w-1/3 mb-4"></div>
        <div className="h-20 bg-indigo-100 rounded mb-4"></div>
        <div className="h-4 bg-indigo-200 rounded w-full"></div>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
        <div className="flex items-center gap-2 text-gray-500">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Análisis de IA no disponible para este mercado aún</span>
        </div>
      </div>
    );
  }

  const confidencePercent = Math.round(prediction.confidence * 100);
  const probPercent = Math.round(prediction.calibrated_probability * 100);
  const lowPercent = Math.round(prediction.probability_low * 100);
  const highPercent = Math.round(prediction.probability_high * 100);

  // Determine stance
  let stance = 'incierto';
  let stanceColor = 'text-gray-700';
  if (prediction.calibrated_probability > 0.6) {
    stance = 'SÍ como probable';
    stanceColor = 'text-green-700';
  } else if (prediction.calibrated_probability < 0.4) {
    stance = 'NO como probable';
    stanceColor = 'text-red-700';
  }

  // Get top factors
  const topFactors = [...prediction.key_factors]
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
    .slice(0, 3);

  // Get highest risk
  const topRisk = prediction.risk_factors.length > 0
    ? [...prediction.risk_factors].sort((a, b) => b.probability - a.probability)[0]
    : null;

  return (
    <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50 rounded-xl p-6 border-2 border-indigo-200 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Análisis de IA</h3>
            <p className="text-xs text-gray-500">
              Actualizado hace {prediction.data_freshness_hours.toFixed(0)}h
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
            confidencePercent >= 70 ? 'bg-green-100 text-green-700' :
            confidencePercent >= 50 ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          }`}>
            {confidencePercent}% confianza
          </span>
        </div>
      </div>

      {/* Main Explanation Card */}
      <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 mb-4 border border-indigo-100">
        <p className="text-gray-800 leading-relaxed">
          Nuestro análisis (<span className="font-semibold">{confidencePercent}% confianza</span>) ve{' '}
          <span className={`font-semibold ${stanceColor}`}>{stance}</span>{' '}
          {topFactors.length > 0 && (
            <>
              debido a{' '}
              <span className="font-semibold">
                {topFactors.map(f => f.factor).join(' y ')}
              </span>
            </>
          )}.
          {topRisk && (
            <>
              {' '}Sin embargo, señalamos <span className="text-orange-600 font-semibold">"{topRisk.risk}"</span> como riesgo.
            </>
          )}
        </p>

        {/* Probability Display */}
        <div className="mt-4 flex items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>NO ({100 - probPercent}%)</span>
              <span>SÍ ({probPercent}%)</span>
            </div>
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden relative">
              {/* Confidence interval background */}
              <div 
                className="absolute h-full bg-indigo-100"
                style={{ 
                  left: `${lowPercent}%`, 
                  width: `${highPercent - lowPercent}%` 
                }}
              />
              {/* Main probability */}
              <div 
                className="h-full bg-gradient-to-r from-red-400 via-gray-400 to-green-400 relative"
              >
                {/* Marker for current probability */}
                <div 
                  className="absolute top-0 w-1 h-full bg-indigo-600 rounded shadow-md"
                  style={{ left: `${probPercent}%`, transform: 'translateX(-50%)' }}
                />
              </div>
            </div>
            <div className="text-center mt-1">
              <span className="text-xs text-gray-500">
                Rango: {lowPercent}% - {highPercent}%
              </span>
            </div>
          </div>
          <div className="text-center px-4 py-2 bg-indigo-100 rounded-lg">
            <div className="text-2xl font-bold text-indigo-700">{probPercent}%</div>
            <div className="text-xs text-indigo-600">Prob. SÍ</div>
          </div>
        </div>
      </div>

      {/* Toggle Details */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center gap-2 text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors"
      >
        <svg 
          className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`} 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
        {showDetails ? 'Ocultar detalles' : 'Ver factores detallados'}
      </button>

      {/* Detailed Factors */}
      {showDetails && (
        <div className="mt-4 space-y-4 animate-fadeIn">
          {/* Key Factors */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Factores Clave
            </h4>
            <div className="space-y-2">
              {prediction.key_factors.map((factor, idx) => (
                <div key={idx} className="bg-white/60 rounded-lg p-3 border border-gray-200">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-800">{factor.factor}</span>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                      factor.impact > 0 ? 'bg-green-100 text-green-700' :
                      factor.impact < 0 ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {factor.impact > 0 ? '+' : ''}{(factor.impact * 100).toFixed(0)}% impacto
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span className="capitalize">{factor.source}</span>
                    <span>{Math.round(factor.confidence * 100)}% confianza</span>
                  </div>
                  {factor.evidence && (
                    <p className="mt-2 text-xs text-gray-600 italic">{factor.evidence}</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Risk Factors */}
          {prediction.risk_factors.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <svg className="w-4 h-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Factores de Riesgo
              </h4>
              <div className="space-y-2">
                {prediction.risk_factors.map((risk, idx) => (
                  <div key={idx} className="bg-orange-50/80 rounded-lg p-3 border border-orange-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-800">{risk.risk}</span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        risk.severity === 'critical' ? 'bg-red-200 text-red-800' :
                        risk.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                        risk.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-gray-200 text-gray-700'
                      }`}>
                        {risk.severity}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">{risk.impact_on_prediction}</p>
                    <div className="mt-1 text-xs text-gray-500">
                      Probabilidad: {Math.round(risk.probability * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reasoning Chain */}
          {prediction.reasoning_chain && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Razonamiento Completo</h4>
              <div className="bg-white/60 rounded-lg p-3 border border-gray-200">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{prediction.reasoning_chain}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

'use client';

import { useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface VoteAggregation {
  total_votes: number;
  yes_votes: number;
  no_votes: number;
  yes_percentage: number;
  no_percentage: number;
  avg_confidence: number;
}

interface UserVote {
  outcome: string;
  confidence: number | null;
  reasoning: string | null;
}

interface VotePanelProps {
  marketId: number;
  isAuthenticated: boolean;
  currentVote?: UserVote | null;
  aggregation?: VoteAggregation | null;
  aiProbability?: number;
  onVoteSubmitted?: () => void;
}

export default function VotePanel({
  marketId,
  isAuthenticated,
  currentVote,
  aggregation,
  aiProbability,
  onVoteSubmitted
}: VotePanelProps) {
  const [selectedOutcome, setSelectedOutcome] = useState<'yes' | 'no' | null>(
    currentVote?.outcome as 'yes' | 'no' | null || null
  );
  const [confidence, setConfidence] = useState<number>(currentVote?.confidence || 3);
  const [reasoning, setReasoning] = useState<string>(currentVote?.reasoning || '');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showReasoning, setShowReasoning] = useState(!!currentVote?.reasoning);

  const getAuthToken = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  };

  const handleSubmit = async () => {
    if (!selectedOutcome) {
      setError('Selecciona SÍ o NO');
      return;
    }

    const token = getAuthToken();
    if (!token) {
      setError('Debes iniciar sesión para votar');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/markets/${marketId}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          outcome: selectedOutcome,
          confidence: confidence,
          reasoning: reasoning.trim() || null
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      // Show success
      if (onVoteSubmitted) {
        onVoteSubmitted();
      }

    } catch (err) {
      console.error('Error voting:', err);
      setError(err instanceof Error ? err.message : 'Error al votar');
    } finally {
      setSubmitting(false);
    }
  };

  // Calculate crowd vs AI comparison
  const crowdProbability = aggregation ? aggregation.yes_percentage / 100 : null;
  const divergence = aiProbability !== undefined && crowdProbability !== null
    ? Math.abs(aiProbability - crowdProbability)
    : null;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Vota tu Predicción
        </h3>
        <p className="text-purple-100 text-sm mt-1">
          Comparte tu perspectiva sin gastar créditos
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Aggregation Stats */}
        {aggregation && aggregation.total_votes > 0 && (
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-600">
                Opinión de la Comunidad
              </span>
              <span className="text-xs text-gray-500">
                {aggregation.total_votes} votos
              </span>
            </div>
            
            {/* Vote Bar */}
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden flex">
              <div 
                className="bg-gradient-to-r from-green-400 to-green-500 transition-all duration-500"
                style={{ width: `${aggregation.yes_percentage}%` }}
              />
              <div 
                className="bg-gradient-to-r from-red-400 to-red-500 transition-all duration-500"
                style={{ width: `${aggregation.no_percentage}%` }}
              />
            </div>
            
            <div className="flex justify-between mt-2 text-sm">
              <span className="text-green-600 font-semibold">
                SÍ: {aggregation.yes_percentage.toFixed(0)}%
              </span>
              <span className="text-red-600 font-semibold">
                NO: {aggregation.no_percentage.toFixed(0)}%
              </span>
            </div>

            {/* AI vs Crowd comparison */}
            {divergence !== null && divergence > 0.1 && (
              <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center gap-2 text-xs text-yellow-800">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>
                    La comunidad ({(crowdProbability! * 100).toFixed(0)}% SÍ) difiere de la IA ({(aiProbability! * 100).toFixed(0)}% SÍ) en {(divergence * 100).toFixed(0)} puntos
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Voting UI */}
        {isAuthenticated ? (
          <>
            {/* Outcome Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                ¿Cuál crees que será el resultado?
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setSelectedOutcome('yes')}
                  className={`py-4 px-6 rounded-xl font-bold text-lg transition-all ${
                    selectedOutcome === 'yes'
                      ? 'bg-green-500 text-white shadow-lg ring-4 ring-green-200 scale-105'
                      : 'bg-green-50 text-green-700 border-2 border-green-200 hover:bg-green-100'
                  }`}
                >
                  SÍ
                </button>
                <button
                  onClick={() => setSelectedOutcome('no')}
                  className={`py-4 px-6 rounded-xl font-bold text-lg transition-all ${
                    selectedOutcome === 'no'
                      ? 'bg-red-500 text-white shadow-lg ring-4 ring-red-200 scale-105'
                      : 'bg-red-50 text-red-700 border-2 border-red-200 hover:bg-red-100'
                  }`}
                >
                  NO
                </button>
              </div>
            </div>

            {/* Confidence Slider */}
            {selectedOutcome && (
              <div className="animate-fadeIn">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  ¿Qué tan seguro estás? (opcional)
                </label>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500">Poco</span>
                  <div className="flex-1">
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={confidence}
                      onChange={(e) => setConfidence(parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between mt-1">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <div 
                          key={n} 
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                            n <= confidence 
                              ? 'bg-purple-500 text-white' 
                              : 'bg-gray-200 text-gray-500'
                          }`}
                        >
                          {n}
                        </div>
                      ))}
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">Muy</span>
                </div>
              </div>
            )}

            {/* Optional Reasoning */}
            {selectedOutcome && (
              <div className="animate-fadeIn">
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="text-sm text-purple-600 hover:text-purple-800 flex items-center gap-1"
                >
                  <svg 
                    className={`w-4 h-4 transition-transform ${showReasoning ? 'rotate-180' : ''}`} 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                  {showReasoning ? 'Ocultar razonamiento' : 'Agregar razonamiento (opcional)'}
                </button>

                {showReasoning && (
                  <textarea
                    value={reasoning}
                    onChange={(e) => setReasoning(e.target.value)}
                    placeholder="¿Por qué crees esto?"
                    rows={3}
                    className="mt-2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    maxLength={500}
                  />
                )}
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={!selectedOutcome || submitting}
              className="w-full py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
            >
              {submitting ? 'Enviando...' : currentVote ? 'Actualizar Voto' : 'Enviar Voto'}
            </button>

            {currentVote && (
              <p className="text-xs text-center text-gray-500">
                Ya votaste <span className="font-semibold">{currentVote.outcome.toUpperCase()}</span>
                {currentVote.confidence && ` con confianza ${currentVote.confidence}/5`}
              </p>
            )}
          </>
        ) : (
          <div className="text-center py-4">
            <p className="text-gray-600 mb-3">Inicia sesión para votar</p>
            <a 
              href="/login" 
              className="inline-block px-6 py-2 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition-colors"
            >
              Iniciar Sesión
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

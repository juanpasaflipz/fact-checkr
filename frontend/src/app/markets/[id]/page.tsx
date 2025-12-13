'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';
import PredictionExplanation from '@/components/features/markets/markets/PredictionExplanation';
import SentimentTimeline from '@/components/features/markets/markets/SentimentTimeline';
import { getApiBaseUrl } from '@/lib/api-config';

interface MarketDetail {
  id: number;
  slug: string;
  question: string;
  description: string | null;
  yes_probability: number;
  no_probability: number;
  yes_liquidity: number;
  no_liquidity: number;
  volume: number;
  created_at: string;
  closes_at: string | null;
  resolved_at: string | null;
  status: string;
  winning_outcome: string | null;
  resolution_source: string | null;
  resolution_criteria: string | null;
  claim_id: string | null;
  category: string | null;
}

interface UserBalance {
  available_credits: number;
  locked_credits: number;
}

export default function MarketDetailPage() {
  const params = useParams();
  const router = useRouter();
  const marketId = params.id as string;
  
  const [market, setMarket] = useState<MarketDetail | null>(null);
  const [balance, setBalance] = useState<UserBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [trading, setTrading] = useState(false);
  const [tradeAmount, setTradeAmount] = useState('');
  const [selectedOutcome, setSelectedOutcome] = useState<'yes' | 'no' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [previewShares, setPreviewShares] = useState<number | null>(null);
  const [previewPrice, setPreviewPrice] = useState<number | null>(null);
  const [predictionData, setPredictionData] = useState<any>(null);
  const [intelligenceData, setIntelligenceData] = useState<any>(null);
  const [loadingIntelligence, setLoadingIntelligence] = useState(true);

  // Get auth token from localStorage
  const getAuthToken = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  };

  const fetchMarket = async () => {
    setLoading(true);
    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/markets/${marketId}`, {
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: MarketDetail = await response.json();
      setMarket(data);
    } catch (error) {
      console.error('Error fetching market:', error);
      setError('No se pudo cargar el mercado');
    } finally {
      setLoading(false);
    }
  };

  const fetchBalance = async () => {
    const token = getAuthToken();
    // Check if token exists and is not empty
    if (!token || token.trim() === '') return;

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/markets/balance`, {
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${token.trim()}`
        }
      });

      if (response.ok) {
        const data: UserBalance = await response.json();
        setBalance(data);
      } else if (response.status === 401 || response.status === 422) {
        // Token is invalid, clear it
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
        }
        setBalance(null);
      }
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const fetchIntelligence = async () => {
    setLoadingIntelligence(true);
    try {
      const baseUrl = getApiBaseUrl();
      
      // Fetch prediction factors
      const predictionResponse = await fetch(`${baseUrl}/api/markets/${marketId}/prediction`, {
        headers: { 'Accept': 'application/json' }
      });
      
      if (predictionResponse.ok) {
        const prediction = await predictionResponse.json();
        setPredictionData(prediction);
      }
      
      // Fetch full intelligence data (includes sentiment and news)
      const intelligenceResponse = await fetch(`${baseUrl}/api/markets/${marketId}/intelligence`, {
        headers: { 'Accept': 'application/json' }
      });
      
      if (intelligenceResponse.ok) {
        const intelligence = await intelligenceResponse.json();
        setIntelligenceData(intelligence);
      }
    } catch (error) {
      console.error('Error fetching intelligence data:', error);
      // Don't show error to user, just log it - intelligence is optional
    } finally {
      setLoadingIntelligence(false);
    }
  };

  useEffect(() => {
    fetchMarket();
    fetchBalance();
    fetchIntelligence();
  }, [marketId]);

  const handleTrade = async () => {
    if (!selectedOutcome || !tradeAmount) {
      setError('Por favor selecciona un resultado y especifica la cantidad');
      return;
    }

    const amount = parseFloat(tradeAmount);
    if (isNaN(amount) || amount <= 0) {
      setError('La cantidad debe ser un número positivo');
      return;
    }

    if (balance && amount > balance.available_credits) {
      setError(`Créditos insuficientes. Disponibles: ${balance.available_credits}`);
      return;
    }

    const token = getAuthToken();
    if (!token) {
      setError('Debes iniciar sesión para realizar operaciones');
      return;
    }

    setTrading(true);
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/markets/${marketId}/trade`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: amount,
          outcome: selectedOutcome
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const tradeResult = await response.json();
      
      // Animate market update
      setMarket(prev => prev ? {
        ...prev,
        yes_probability: tradeResult.market.yes_probability,
        no_probability: tradeResult.market.no_probability,
        volume: tradeResult.market.volume
      } : null);
      
      setBalance(prev => prev ? {
        ...prev,
        available_credits: tradeResult.user_balance
      } : null);
      
      // Reset form
      setTradeAmount('');
      setSelectedOutcome(null);
      setPreviewShares(null);
      setPreviewPrice(null);
      
      // Show success toast (better UX than alert)
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 animate-slideIn';
      toast.innerHTML = `
        <div class="flex items-center gap-3">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <div>
            <div class="font-semibold">Perspectiva registrada</div>
            <div class="text-sm opacity-90">${tradeResult.shares.toFixed(2)} acciones de ${selectedOutcome.toUpperCase()} a ${tradeResult.price.toFixed(4)} créditos</div>
          </div>
        </div>
      `;
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
      }, 3000);
    } catch (error) {
      console.error('Error trading:', error);
      setError(error instanceof Error ? error.message : 'Error al realizar la operación');
    } finally {
      setTrading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA]">
        <Sidebar />
        <div className="lg:pl-64">
          <Header searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSearch={() => {}} />
          <main className="p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
              <div className="flex flex-col items-center justify-center py-24">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-blue-100 rounded-full"></div>
                  <div className="w-16 h-16 border-4 border-[#2563EB] border-t-transparent rounded-full animate-spin absolute top-0"></div>
                </div>
                <p className="mt-6 text-gray-600 font-medium animate-pulse">Cargando mercado...</p>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (error && !market) {
    return (
      <div className="min-h-screen bg-[#F8F9FA]">
        <Sidebar />
        <div className="lg:pl-64">
          <Header searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSearch={() => {}} />
          <main className="p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <p className="text-red-700 font-semibold">{error}</p>
                <button
                  onClick={() => router.push('/markets')}
                  className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Volver a mercados
                </button>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (!market) return null;

  const isAuthenticated = !!getAuthToken();
  const isOpen = market.status === 'open';

  return (
    <div className="min-h-screen bg-[#F8F9FA]">
      <Sidebar />
      <div className="lg:pl-64">
        <Header searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSearch={() => {}} />
        <main className="p-6 lg:p-8">
          <div className="max-w-4xl mx-auto space-y-6">
            
            {/* Back Button */}
            <button
              onClick={() => router.push('/markets')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Volver a mercados
            </button>

            {/* Market Card */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
              <div className="flex items-start justify-between mb-4">
                <h1 className="text-2xl font-bold text-gray-900 flex-1">{market.question}</h1>
                <span className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold ${
                  market.status === 'open' 
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : market.status === 'resolved'
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200'
                }`}>
                  {market.status === 'open' ? 'Abierto' : market.status === 'resolved' ? 'Resuelto' : 'Cancelado'}
                </span>
              </div>

              {/* Category Badge */}
              {market.category && (
                <div className="mb-4">
                  <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                    {market.category === 'politics' ? 'Política' :
                     market.category === 'economy' ? 'Economía' :
                     market.category === 'security' ? 'Seguridad' :
                     market.category === 'rights' ? 'Derechos' :
                     market.category === 'environment' ? 'Medio Ambiente' :
                     market.category === 'mexico-us-relations' ? 'México-Estados Unidos' :
                     market.category === 'institutions' ? 'Instituciones' :
                     market.category}
                  </span>
                </div>
              )}

              {market.description && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm font-medium text-gray-600 mb-1">Contexto</p>
                  <p className="text-gray-700 leading-relaxed">{market.description}</p>
                </div>
              )}

              {/* Resolution Criteria */}
              {market.resolution_criteria && (
                <div className="mb-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm font-semibold text-amber-900">Criterios de Resolución</p>
                  </div>
                  <p className="text-sm text-amber-800 leading-relaxed">{market.resolution_criteria}</p>
                </div>
              )}

              {/* Probabilities - More Prominent with Animation */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-300 rounded-xl p-5 shadow-sm transition-all duration-500">
                  <div className="text-xs font-semibold text-green-700 mb-2 uppercase tracking-wide">Probabilidad de SÍ</div>
                  <div className="text-4xl font-bold text-green-700 mb-1 transition-all duration-500" key={market.yes_probability}>
                    {(market.yes_probability * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-green-600">Basado en la inteligencia colectiva</div>
                </div>
                <div className="bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 rounded-xl p-5 shadow-sm transition-all duration-500">
                  <div className="text-xs font-semibold text-red-700 mb-2 uppercase tracking-wide">Probabilidad de NO</div>
                  <div className="text-4xl font-bold text-red-700 mb-1 transition-all duration-500" key={market.no_probability}>
                    {(market.no_probability * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-red-600">Basado en la inteligencia colectiva</div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mb-6 text-sm">
                <div>
                  <div className="text-gray-600 font-medium">Volumen</div>
                  <div className="text-gray-900 font-semibold">
                    {market.volume.toLocaleString('es-MX', { maximumFractionDigits: 0 })} créditos
                  </div>
                </div>
                <div>
                  <div className="text-gray-600 font-medium">Liquidez SÍ</div>
                  <div className="text-gray-900 font-semibold">
                    {market.yes_liquidity.toLocaleString('es-MX', { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div>
                  <div className="text-gray-600 font-medium">Liquidez NO</div>
                  <div className="text-gray-900 font-semibold">
                    {market.no_liquidity.toLocaleString('es-MX', { maximumFractionDigits: 0 })}
                  </div>
                </div>
              </div>

              {/* Resolution Info */}
              {market.status === 'resolved' && market.winning_outcome && (
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-300 rounded-xl p-5 mb-6 shadow-sm">
                  <div className="flex items-center gap-2 mb-3">
                    <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="font-bold text-blue-900 text-lg">
                      Resultado: {market.winning_outcome.toUpperCase()}
                    </div>
                  </div>
                  {market.resolution_source && (
                    <div className="mb-2">
                      <div className="text-xs font-semibold text-blue-700 mb-1 uppercase tracking-wide">Fuente de Resolución</div>
                      <div className="text-sm text-blue-800 bg-white/50 rounded px-3 py-2 border border-blue-200">
                        {market.resolution_source}
                      </div>
                    </div>
                  )}
                  {market.resolved_at && (
                    <div className="text-xs text-blue-600 mt-2">
                      Resuelto el {formatDate(market.resolved_at)}
                    </div>
                  )}
                </div>
              )}

              {/* Trading Panel */}
              {isOpen && isAuthenticated && (
                <div className="border-t border-gray-200 pt-6 mt-6">
                  <div className="mb-4">
                    <h2 className="text-lg font-semibold text-gray-900 mb-1">Expresar tu Perspectiva</h2>
                    <p className="text-sm text-gray-600">
                      Usa créditos virtuales para indicar tu perspectiva sobre este tema. 
                      No es apuesta; es inteligencia colectiva.
                    </p>
                  </div>
                  
                  {balance && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                      <div className="text-sm text-gray-600">Créditos disponibles:</div>
                      <div className="text-xl font-bold text-gray-900">{balance.available_credits.toFixed(2)}</div>
                    </div>
                  )}

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Selecciona tu perspectiva
                      </label>
                      <div className="flex gap-3">
                        <button
                          onClick={() => setSelectedOutcome('yes')}
                          className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                            selectedOutcome === 'yes'
                              ? 'bg-green-600 text-white shadow-md ring-2 ring-green-300'
                              : 'bg-green-50 text-green-700 border-2 border-green-200 hover:bg-green-100 hover:border-green-300'
                          }`}
                        >
                          SÍ
                        </button>
                        <button
                          onClick={() => setSelectedOutcome('no')}
                          className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                            selectedOutcome === 'no'
                              ? 'bg-red-600 text-white shadow-md ring-2 ring-red-300'
                              : 'bg-red-50 text-red-700 border-2 border-red-200 hover:bg-red-100 hover:border-red-300'
                          }`}
                        >
                          NO
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Cantidad de créditos
                      </label>
                      <input
                        type="number"
                        value={tradeAmount}
                        onChange={(e) => {
                          setTradeAmount(e.target.value);
                          // Calculate preview
                          const amount = parseFloat(e.target.value);
                          if (!isNaN(amount) && amount > 0 && selectedOutcome && market) {
                            // Estimate shares based on current probability (simplified)
                            const currentProb = selectedOutcome === 'yes' ? market.yes_probability : market.no_probability;
                            const estimatedShares = amount / currentProb; // Rough estimate
                            const estimatedPrice = amount / estimatedShares;
                            setPreviewShares(estimatedShares);
                            setPreviewPrice(estimatedPrice);
                          } else {
                            setPreviewShares(null);
                            setPreviewPrice(null);
                          }
                        }}
                        placeholder="0.00"
                        min="0"
                        step="0.01"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#2563EB] focus:border-transparent transition-all"
                      />
                      
                      {/* Preview */}
                      {previewShares && previewPrice && selectedOutcome && (
                        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg animate-fadeIn">
                          <div className="text-xs text-blue-700 font-medium mb-1">Vista previa:</div>
                          <div className="text-sm text-blue-900">
                            Recibirías aproximadamente <span className="font-bold">{previewShares.toFixed(2)}</span> acciones 
                            {' '}de <span className="font-bold">{selectedOutcome.toUpperCase()}</span> 
                            {' '}a <span className="font-bold">{previewPrice.toFixed(4)}</span> créditos cada una
                          </div>
                        </div>
                      )}
                    </div>

                    {error && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
                        {error}
                      </div>
                    )}

                    <button
                      onClick={handleTrade}
                      disabled={trading || !selectedOutcome || !tradeAmount}
                      className="w-full py-3 px-4 bg-[#2563EB] text-white font-semibold rounded-lg hover:bg-[#1d4ed8] disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md hover:shadow-lg"
                    >
                      {trading ? 'Procesando...' : 'Confirmar Perspectiva'}
                    </button>
                  </div>
                </div>
              )}

              {isOpen && !isAuthenticated && (
                <div className="border-t border-gray-200 pt-6 mt-6 text-center">
                  <p className="text-gray-600 mb-1">Inicia sesión para expresar tu perspectiva</p>
                  <p className="text-sm text-gray-500 mb-4">Contribuye a la inteligencia colectiva sobre el futuro de México</p>
                  <button
                    onClick={() => router.push('/api/auth/login')}
                    className="px-6 py-2 bg-[#2563EB] text-white font-semibold rounded-lg hover:bg-[#1d4ed8] shadow-md hover:shadow-lg transition-all"
                  >
                    Iniciar Sesión
                  </button>
                </div>
              )}
            </div>

            {/* AI Intelligence Section */}
            <div className="space-y-6">
              {/* Prediction Explanation */}
              <PredictionExplanation 
                prediction={predictionData ? {
                  raw_probability: predictionData.raw_probability,
                  calibrated_probability: predictionData.calibrated_probability,
                  confidence: predictionData.confidence,
                  probability_low: predictionData.probability_low || predictionData.calibrated_probability - 0.1,
                  probability_high: predictionData.probability_high || predictionData.calibrated_probability + 0.1,
                  key_factors: predictionData.key_factors || [],
                  risk_factors: predictionData.risk_factors || [],
                  reasoning_chain: predictionData.reasoning_chain,
                  summary: predictionData.summary,
                  data_freshness_hours: predictionData.data_freshness_hours || 24,
                  analysis_tier: predictionData.analysis_tier || 2
                } : null}
                loading={loadingIntelligence}
              />

              {/* Sentiment Timeline */}
              <SentimentTimeline 
                sentiment={intelligenceData?.sentiment_data || null}
                news={intelligenceData?.news_data || null}
                loading={loadingIntelligence}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}


'use client';

interface SentimentData {
  posts_analyzed: number;
  weighted_sentiment: number;
  raw_sentiment: number;
  sentiment_confidence: number;
  momentum: number;
  volume_trend: number;
  platform_breakdown: Record<string, number>;
  freshness_hours: number;
  bot_filtered_count: number;
}

interface NewsData {
  volume: number;
  overall_signal: number;
  credibility_weighted_signal: number;
  freshness_hours: number;
}

interface SentimentTimelineProps {
  sentiment?: SentimentData | null;
  news?: NewsData | null;
  loading?: boolean;
}

export default function SentimentTimeline({ sentiment, news, loading }: SentimentTimelineProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-32 bg-gray-100 rounded"></div>
      </div>
    );
  }

  const hasSentiment = sentiment && sentiment.posts_analyzed > 0;
  const hasNews = news && news.volume > 0;

  if (!hasSentiment && !hasNews) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
          Señales de Datos
        </h3>
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p>No hay datos de sentimiento disponibles aún</p>
        </div>
      </div>
    );
  }

  // Helper to render sentiment bar
  const renderSentimentBar = (value: number, label: string) => {
    const percentage = ((value + 1) / 2) * 100; // Convert -1 to 1 -> 0 to 100
    const isPositive = value > 0;
    const isNegative = value < 0;

    return (
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-gray-600">{label}</span>
          <span className={`font-semibold ${
            isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'
          }`}>
            {value > 0 ? '+' : ''}{(value * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden relative">
          {/* Center marker */}
          <div className="absolute top-0 left-1/2 w-0.5 h-full bg-gray-400 transform -translate-x-1/2" />
          {/* Value bar */}
          <div 
            className={`h-full transition-all duration-500 ${
              isPositive ? 'bg-gradient-to-r from-gray-300 to-green-500' : 
              isNegative ? 'bg-gradient-to-l from-gray-300 to-red-500' : 
              'bg-gray-300'
            }`}
            style={{
              width: `${Math.abs(value) * 50}%`,
              marginLeft: isPositive ? '50%' : `${50 - Math.abs(value) * 50}%`
            }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-cyan-500 px-6 py-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
          Señales de Datos
        </h3>
        <p className="text-blue-100 text-sm mt-1">
          Análisis de sentimiento y noticias en tiempo real
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Social Sentiment Section */}
        {hasSentiment && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
              </svg>
              Sentimiento en Redes Sociales
            </h4>

            {/* Main Sentiment */}
            {renderSentimentBar(sentiment!.weighted_sentiment, 'Sentimiento General')}

            {/* Momentum */}
            <div className="mt-3">
              {renderSentimentBar(sentiment!.momentum, 'Momentum (tendencia)')}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-gray-900">
                  {sentiment!.posts_analyzed}
                </div>
                <div className="text-xs text-gray-500">Posts analizados</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-gray-900">
                  {Math.round(sentiment!.sentiment_confidence * 100)}%
                </div>
                <div className="text-xs text-gray-500">Confianza</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-gray-900">
                  {sentiment!.bot_filtered_count}
                </div>
                <div className="text-xs text-gray-500">Bots filtrados</div>
              </div>
            </div>

            {/* Platform Breakdown */}
            {Object.keys(sentiment!.platform_breakdown).length > 0 && (
              <div className="mt-4">
                <h5 className="text-xs font-semibold text-gray-600 mb-2">Por Plataforma</h5>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(sentiment!.platform_breakdown).map(([platform, value]) => (
                    <div 
                      key={platform}
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        value > 0.1 ? 'bg-green-100 text-green-700' :
                        value < -0.1 ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {platform}: {value > 0 ? '+' : ''}{(value * 100).toFixed(0)}%
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-xs text-gray-400 mt-2">
              Actualizado hace {sentiment!.freshness_hours.toFixed(1)}h
            </div>
          </div>
        )}

        {/* Divider */}
        {hasSentiment && hasNews && (
          <hr className="border-gray-200" />
        )}

        {/* News Section */}
        {hasNews && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
              </svg>
              Señal de Noticias
            </h4>

            {/* News Signal */}
            {renderSentimentBar(news!.credibility_weighted_signal, 'Señal de Noticias (ponderada)')}

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div className="bg-orange-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-orange-700">
                  {news!.volume}
                </div>
                <div className="text-xs text-orange-600">Artículos</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-orange-700">
                  {news!.freshness_hours.toFixed(1)}h
                </div>
                <div className="text-xs text-orange-600">Antigüedad</div>
              </div>
            </div>
          </div>
        )}

        {/* Combined Signal */}
        {hasSentiment && hasNews && (
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-4 border border-indigo-200">
            <h4 className="text-sm font-semibold text-indigo-700 mb-2">Señal Combinada</h4>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                {renderSentimentBar(
                  (sentiment!.weighted_sentiment * 0.6 + news!.credibility_weighted_signal * 0.4),
                  'Señal Total'
                )}
              </div>
            </div>
            <p className="text-xs text-indigo-600 mt-2">
              60% sentimiento social + 40% señal de noticias
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

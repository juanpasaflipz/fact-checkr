'use client';

import Link from 'next/link';

interface Topic {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
}

interface TopicStats {
  total_claims?: number;
  verified_count?: number;
  debunked_count?: number;
  misleading_count?: number;
  unverified_count?: number;
}

interface TopicCardProps {
  topic: Topic;
  stats?: TopicStats;
  showDescription?: boolean;
  variant?: 'default' | 'compact' | 'detailed';
}

export default function TopicCard({ 
  topic, 
  stats, 
  showDescription = false,
  variant = 'default' 
}: TopicCardProps) {
  const totalClaims = stats?.total_claims || 0;
  const verifiedCount = stats?.verified_count || 0;
  const debunkedCount = stats?.debunked_count || 0;
  const misleadingCount = stats?.misleading_count || 0;
  const unverifiedCount = stats?.unverified_count || 0;
  
  const fakeNewsCount = debunkedCount + misleadingCount;
  const verifiedPercentage = totalClaims > 0 ? Math.round((verifiedCount / totalClaims) * 100) : 0;
  const fakeNewsPercentage = totalClaims > 0 ? Math.round((fakeNewsCount / totalClaims) * 100) : 0;

  if (variant === 'compact') {
    return (
      <Link
        href={`/temas/${topic.slug}`}
        className="group block p-4 bg-white rounded-xl border border-gray-200 hover:border-[#2563EB] hover:shadow-md transition-all duration-200"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 group-hover:text-[#2563EB] transition-colors truncate">
              {topic.name}
            </h3>
            {totalClaims > 0 && (
              <p className="text-sm text-gray-500 mt-1">{totalClaims.toLocaleString('es-MX')} afirmaciones</p>
            )}
          </div>
          <svg className="w-5 h-5 text-gray-400 group-hover:text-[#2563EB] transition-colors flex-shrink-0 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </Link>
    );
  }

  if (variant === 'detailed') {
    return (
      <Link
        href={`/temas/${topic.slug}`}
        className="group block p-6 bg-gradient-to-br from-white to-gray-50 rounded-2xl border border-gray-200 hover:border-[#2563EB] hover:shadow-lg transition-all duration-200"
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-[#2563EB] transition-colors mb-2">
              {topic.name}
            </h3>
            {topic.description && (
              <p className="text-sm text-gray-600 line-clamp-2">{topic.description}</p>
            )}
          </div>
          <div className="ml-4 flex-shrink-0">
            <div className="size-12 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#1e40af] flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
              </svg>
            </div>
          </div>
        </div>

        {stats && totalClaims > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-gray-900">{totalClaims.toLocaleString('es-MX')}</span>
              <span className="text-sm text-gray-500">afirmaciones totales</span>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-200">
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-green-500"></div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500">Verificadas</p>
                  <p className="text-sm font-semibold text-gray-900">{verifiedCount} ({verifiedPercentage}%)</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="size-2 rounded-full bg-red-500"></div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500">Fake News</p>
                  <p className="text-sm font-semibold text-gray-900">{fakeNewsCount} ({fakeNewsPercentage}%)</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {totalClaims === 0 && (
          <div className="pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-500">Sin afirmaciones aún</p>
          </div>
        )}
      </Link>
    );
  }

  // Default variant
  return (
    <Link
      href={`/temas/${topic.slug}`}
      className="group block p-5 bg-white rounded-xl border border-gray-200 hover:border-[#2563EB] hover:shadow-md transition-all duration-200"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 group-hover:text-[#2563EB] transition-colors mb-1">
            {topic.name}
          </h3>
          {showDescription && topic.description && (
            <p className="text-sm text-gray-600 line-clamp-2 mt-1">{topic.description}</p>
          )}
        </div>
        <svg className="w-5 h-5 text-gray-400 group-hover:text-[#2563EB] transition-colors flex-shrink-0 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>

      {stats && totalClaims > 0 ? (
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div>
            <p className="text-lg font-bold text-gray-900">{totalClaims.toLocaleString('es-MX')}</p>
            <p className="text-xs text-gray-500">afirmaciones</p>
          </div>
          <div className="flex items-center gap-4">
            {verifiedCount > 0 && (
              <div className="text-right">
                <p className="text-sm font-semibold text-green-600">{verifiedCount}</p>
                <p className="text-xs text-gray-500">verificadas</p>
              </div>
            )}
            {fakeNewsCount > 0 && (
              <div className="text-right">
                <p className="text-sm font-semibold text-red-600">{fakeNewsCount}</p>
                <p className="text-xs text-gray-500">fake news</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="pt-3 border-t border-gray-100">
          <p className="text-sm text-gray-500">Sin afirmaciones aún</p>
        </div>
      )}
    </Link>
  );
}


'use client';

interface Source {
  id: string;
  platform: string;
  content: string;
  author: string | null;
  url: string | null;
  timestamp: string;
  scraped_at: string;
  processed: number; // 0 = pending, 1 = processed, 2 = skipped
  claim_count: number;
}

interface SourceCardProps {
  source: Source;
}

const platformColors: { [key: string]: string } = {
  'Twitter': 'bg-blue-50 text-blue-700 border-blue-200',
  'X': 'bg-gray-50 text-gray-700 border-gray-200',
  'Reddit': 'bg-orange-50 text-orange-700 border-orange-200',
  'Google News': 'bg-green-50 text-green-700 border-green-200',
  'Facebook': 'bg-blue-50 text-blue-700 border-blue-200',
  'Instagram': 'bg-pink-50 text-pink-700 border-pink-200',
};

const processStatusLabels: { [key: number]: { label: string; color: string } } = {
  0: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-800' },
  1: { label: 'Procesado', color: 'bg-green-100 text-green-800' },
  2: { label: 'Omitido', color: 'bg-gray-100 text-gray-800' },
};

export default function SourceCard({ source }: SourceCardProps) {
  const platformColor = platformColors[source.platform] || 'bg-gray-50 text-gray-700 border-gray-200';
  const statusInfo = processStatusLabels[source.processed] || processStatusLabels[0];
  
  // Format timestamp
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-MX', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  // Truncate content for preview
  const contentPreview = source.content.length > 300 
    ? `${source.content.substring(0, 300)}...` 
    : source.content;

  return (
    <article className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-lg text-xs font-semibold border ${platformColor}`}>
            {source.platform}
          </span>
          <span className={`px-2 py-1 rounded-md text-xs font-medium ${statusInfo.color}`}>
            {statusInfo.label}
          </span>
          {source.claim_count > 0 && (
            <span className="px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
              {source.claim_count} {source.claim_count === 1 ? 'afirmación' : 'afirmaciones'}
            </span>
          )}
        </div>
        {source.url && (
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#2563EB] hover:text-[#1e40af] transition-colors"
            title="Ver fuente original"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        )}
      </div>

      {/* Author */}
      {source.author && (
        <div className="mb-3">
          <p className="text-sm text-gray-600 font-medium">
            <span className="text-gray-500">Por:</span> {source.author}
          </p>
        </div>
      )}

      {/* Content */}
      <div className="mb-4">
        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
          {contentPreview}
        </p>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-4">
          <span>Publicado: {formatDate(source.timestamp)}</span>
          {source.scraped_at && (
            <span>Escrapeado: {formatDate(source.scraped_at)}</span>
          )}
        </div>
        <span className="text-gray-400">ID: {source.id.substring(0, 8)}...</span>
      </div>
    </article>
  );
}


import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { addToHistory } from '@/lib/claimHistory';
import { getApiBaseUrl } from '@/lib/api-config';

type VerificationStatus = "Verified" | "Debunked" | "Misleading" | "Unverified";

interface EvidenceDetail {
  url: string;
  snippet?: string;
  timestamp?: string | null;
  relevance_score?: number | null;
  title?: string | null;
  domain?: string | null;
}

interface ClaimProps {
  claim: {
    id: string;
    claim_text: string;
    original_text: string;
    verification: {
      status: VerificationStatus;
      explanation: string;
      sources: string[];
      evidence_details?: EvidenceDetail[];
    } | null;
    source_post: {
      platform: string;
      author: string;
      url: string;
      timestamp: string;
    } | null;
    market?: {
      id: number;
      slug: string;
      question: string;
      yes_probability: number;
      no_probability: number;
      volume: number;
      closes_at: string | null;
      status: string;
      claim_id: string | null;
    } | null;
  };
}

const statusConfig = {
  Verified: {
    label: 'Verificado',
    icon: 'ShieldCheck',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    accent: 'border-l-emerald-500',
    color: 'emerald',
  },
  Debunked: {
    label: 'Falso',
    icon: 'ShieldAlert',
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
    accent: 'border-l-rose-500',
    color: 'rose',
  },
  Misleading: {
    label: 'Engañoso',
    icon: 'AlertTriangle',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    accent: 'border-l-amber-500',
    color: 'amber',
  },
  Unverified: {
    label: 'Sin Verificar',
    icon: 'Clock',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    accent: 'border-l-blue-500',
    color: 'blue',
  },
};

export default function ClaimCard({ claim }: ClaimProps) {
  const router = useRouter();
  const status = claim.verification?.status || "Unverified";
  const config = statusConfig[status];
  const StatusIcon = config.icon;
  const [sharing, setSharing] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);
  const [readingLevel, setReadingLevel] = useState<'simple' | 'normal' | 'expert'>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('reading_level') as 'simple' | 'normal' | 'expert') || 'normal';
    }
    return 'normal';
  });

  // Add claim to history when component mounts (when claim is viewed)
  useEffect(() => {
    addToHistory({
      id: claim.id,
      claim_text: claim.claim_text,
      verification: claim.verification,
    });
  }, [claim.id, claim.claim_text, claim.verification]);

  const handleShare = async (type: 'tweet' | 'image') => {
    if (type === 'tweet') {
      setSharing(true);
      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/share/claim/${claim.id}`, {
          headers: { 'Accept': 'application/json' }
        });
        
        if (response.ok) {
          const data = await response.json();
          
          // Copy to clipboard
          if (navigator.clipboard) {
            await navigator.clipboard.writeText(data.tweet_text);
            setShareSuccess(true);
            setTimeout(() => setShareSuccess(false), 2000);
          } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = data.tweet_text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            setShareSuccess(true);
            setTimeout(() => setShareSuccess(false), 2000);
          }
        }
      } catch (error) {
        console.error('Error sharing:', error);
      } finally {
        setSharing(false);
      }
    } else if (type === 'image') {
      // For image sharing, we'll create a simple canvas-based image
      // This is a simplified version - in production you'd want server-side image generation
      alert('Compartir como imagen próximamente. Por ahora usa "Copiar para Tweet".');
    }
  };

  return (
    <article className={`
      group relative p-6 
      bg-white 
      border-l-4 ${config.accent}
      border-t border-r border-b border-gray-200
      transition-all duration-200 
      hover:shadow-md hover:border-gray-300
      rounded-lg
    `}>
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="
            size-10 rounded-lg 
            bg-gray-100 
            flex items-center justify-center flex-shrink-0
            border border-gray-200
            group-hover:bg-gray-200 transition-colors duration-200
          ">
            <svg className="size-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-gray-900 truncate font-semibold">
              {claim.source_post?.author || "Desconocido"}
            </p>
            <p className="text-xs text-gray-500">{claim.source_post?.platform || "Unknown"}</p>
          </div>
        </div>
        
        <span className={`
          inline-flex items-center gap-1.5 px-3 py-1.5 
          rounded-lg text-xs font-semibold border 
          ${config.badge} 
          transition-all duration-200
        `}>
          <Icon name={StatusIcon} className="size-4" />
          {config.label}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-gray-900 mb-4 line-clamp-2 font-semibold text-lg leading-relaxed">
        "{claim.claim_text}"
      </h3>

      {/* Origin */}
      {claim.original_text !== claim.claim_text && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 mb-2 font-semibold uppercase tracking-wide">ORIGEN</p>
          <p className="text-sm text-gray-700 line-clamp-2 leading-relaxed">{claim.original_text}</p>
        </div>
      )}

      {/* Analysis */}
      {claim.verification && (
        <>
          <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-gray-600 font-semibold uppercase tracking-wide">ANÁLISIS DE FACTCHECKR</p>
              <div className="flex items-center gap-2">
                <label htmlFor={`reading-level-${claim.id}`} className="text-xs text-gray-600">
                  Nivel:
                </label>
                <select
                  id={`reading-level-${claim.id}`}
                  value={readingLevel}
                  onChange={(e) => {
                    const newLevel = e.target.value as 'simple' | 'normal' | 'expert';
                    setReadingLevel(newLevel);
                    if (typeof window !== 'undefined') {
                      localStorage.setItem('reading_level', newLevel);
                    }
                  }}
                  className="text-xs px-2 py-1 bg-white border border-gray-300 rounded text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-900"
                >
                  <option value="simple">Simple (ELI12)</option>
                  <option value="normal">Normal (ELI18)</option>
                  <option value="expert">Experto</option>
                </select>
              </div>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{claim.verification.explanation}</p>
            {readingLevel !== 'normal' && (
              <p className="text-xs text-gray-500 mt-2 italic">
                {readingLevel === 'simple' 
                  ? 'Nota: La explicación se mostrará en nivel simple próximamente.'
                  : 'Nota: La explicación experta estará disponible próximamente.'}
              </p>
            )}
          </div>

          {/* Sources - Enhanced with evidence_details if available */}
          {claim.verification.sources.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-gray-600 mb-3 font-semibold uppercase tracking-wide">FUENTES</p>
              <div className="space-y-3">
                {claim.verification.evidence_details && claim.verification.evidence_details.length > 0 ? (
                  // Rich evidence details with snippets
                  claim.verification.evidence_details.map((evidence, index) => {
                    const hostname = evidence.domain || (() => {
                      try {
                        return new URL(evidence.url).hostname.replace('www.', '');
                      } catch {
                        return evidence.url;
                      }
                    })();
                    
                    return (
                      <div
                        key={index}
                        className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:border-gray-300 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <a
                            href={evidence.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-sm font-semibold text-gray-900 hover:text-blue-600 transition-colors flex-1 min-w-0"
                          >
                            <svg className="size-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                            <span className="truncate">{evidence.title || hostname}</span>
                          </a>
                          {evidence.relevance_score !== null && evidence.relevance_score !== undefined && (
                            <span className="text-xs text-gray-500 flex-shrink-0">
                              {(evidence.relevance_score * 100).toFixed(0)}% relevante
                            </span>
                          )}
                        </div>
                        {evidence.snippet && (
                          <p className="text-xs text-gray-600 leading-relaxed line-clamp-2 mb-2">
                            {evidence.snippet}
                          </p>
                        )}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span className="truncate">{hostname}</span>
                          {evidence.timestamp && (
                            <>
                              <span>•</span>
                              <span>{new Date(evidence.timestamp).toLocaleDateString('es-MX')}</span>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  // Fallback to simple source links
                  claim.verification.sources.map((source, index) => {
                    try {
                      const hostname = new URL(source).hostname.replace('www.', '');
                      return (
                        <a
                          key={index}
                          href={source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="
                            inline-flex items-center gap-1.5 px-3 py-1.5 
                            text-xs text-gray-700 
                            bg-gray-50 
                            hover:bg-gray-100
                            rounded-lg transition-colors duration-200 
                            border border-gray-200 
                            font-medium
                          "
                        >
                          <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          {hostname}
                        </a>
                      );
                    } catch (e) {
                      return null;
                    }
                  })
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Market Signal */}
      {claim.market && claim.market.status === 'open' && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="text-xs font-semibold text-gray-900 uppercase tracking-wide">Señal del Mercado</span>
              </div>
              <span className="text-xs text-gray-600 font-medium">
                Lo que piensa la gente informada
              </span>
            </div>
            
            {/* Probability Bar */}
            <div className="mb-3">
              <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full flex">
                  <div
                    className="bg-emerald-500 transition-all duration-500"
                    style={{ 
                      width: `${claim.market.yes_probability * 100}%`,
                    }}
                  />
                  <div
                    className="bg-rose-500 transition-all duration-500"
                    style={{ 
                      width: `${claim.market.no_probability * 100}%`,
                    }}
                  />
                </div>
              </div>
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-600">SÍ:</span>
                  <span className="text-base font-semibold text-emerald-700">
                    {(claim.market.yes_probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-600">NO:</span>
                  <span className="text-base font-semibold text-rose-700">
                    {(claim.market.no_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                router.push(`/markets/${claim.market!.id}`);
              }}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold text-white bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors duration-200"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Ver y participar en el mercado
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </article>
  );
}

function Icon({ name, className }: { name: string; className?: string }) {
  switch (name) {
    case "ShieldCheck":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>;
    case "ShieldAlert":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>;
    case "AlertTriangle":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>;
    case "Clock":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
    default:
      return null;
  }
}

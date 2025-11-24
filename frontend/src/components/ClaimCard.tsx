import React from 'react';

type VerificationStatus = "Verified" | "Debunked" | "Misleading" | "Unverified";

interface ClaimProps {
  claim: {
    id: string;
    claim_text: string;
    original_text: string;
    verification: {
      status: VerificationStatus;
      explanation: string;
      sources: string[];
    } | null;
    source_post: {
      platform: string;
      author: string;
      url: string;
      timestamp: string;
    } | null;
  };
}

const statusConfig = {
  Verified: {
    label: 'Verificado',
    icon: 'ShieldCheck',
    badge: 'bg-green-100 text-green-700 border-green-200',
    accent: 'border-l-green-500',
  },
  Debunked: {
    label: 'Falso',
    icon: 'ShieldAlert',
    badge: 'bg-red-100 text-red-700 border-red-200',
    accent: 'border-l-red-500',
  },
  Misleading: {
    label: 'Engañoso',
    icon: 'AlertTriangle',
    badge: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    accent: 'border-l-yellow-500',
  },
  Unverified: {
    label: 'Sin Verificar',
    icon: 'Clock',
    badge: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    accent: 'border-l-yellow-500',
  },
};

export default function ClaimCard({ claim }: ClaimProps) {
  const status = claim.verification?.status || "Unverified";
  const config = statusConfig[status];
  const StatusIcon = config.icon;

  return (
    <article className={`p-6 hover:bg-gray-50/50 transition-colors border-l-4 ${config.accent} bg-white`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="size-10 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center flex-shrink-0">
            <svg className="size-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-gray-900 truncate font-semibold">{claim.source_post?.author || "Desconocido"}</p>
            <p className="text-xs text-gray-500">{claim.source_post?.platform || "Unknown"}</p>
          </div>
        </div>
        
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold border ${config.badge} shadow-sm`}>
          <Icon name={StatusIcon} className="size-3.5" />
          {config.label}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-gray-900 mb-3 line-clamp-2 font-semibold text-base">
        "{claim.claim_text}"
      </h3>

      {/* Origin */}
      {claim.original_text !== claim.claim_text && (
        <div className="mb-4 p-3 bg-[#F8F9FA] rounded-lg border border-gray-200">
          <p className="text-xs text-gray-500 mb-1 font-semibold uppercase">ORIGEN</p>
          <p className="text-sm text-gray-700 line-clamp-2">{claim.original_text}</p>
        </div>
      )}

      {/* Analysis */}
      {claim.verification && (
        <>
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-2 font-semibold uppercase">ANÁLISIS DE FACTCHECKR</p>
            <p className="text-sm text-gray-700 leading-relaxed">{claim.verification.explanation}</p>
          </div>

          {/* Sources */}
          {claim.verification.sources.length > 0 && (
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs text-gray-500 font-medium">Fuentes:</span>
              {claim.verification.sources.map((source, index) => {
                try {
                  const hostname = new URL(source).hostname.replace('www.', '');
                  return (
                    <a
                      key={index}
                      href={source}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#2563EB] bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200 font-medium"
                    >
                      <svg className="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      {hostname}
                    </a>
                  );
                } catch (e) {
                  return null;
                }
              })}
            </div>
          )}
        </>
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

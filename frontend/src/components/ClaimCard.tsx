import React from 'react';
import { useRouter } from 'next/navigation';

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
    badge: 'bg-[#1a1a24] text-[#00ff88] border-[#00ff88]',
    accent: 'border-l-[#00ff88]',
    neon: '#00ff88',
  },
  Debunked: {
    label: 'Falso',
    icon: 'ShieldAlert',
    badge: 'bg-[#1a1a24] text-[#ff00ff] border-[#ff00ff]',
    accent: 'border-l-[#ff00ff]',
    neon: '#ff00ff',
  },
  Misleading: {
    label: 'Engañoso',
    icon: 'AlertTriangle',
    badge: 'bg-[#1a1a24] text-[#ffaa00] border-[#ffaa00]',
    accent: 'border-l-[#ffaa00]',
    neon: '#ffaa00',
  },
  Unverified: {
    label: 'Sin Verificar',
    icon: 'Clock',
    badge: 'bg-[#1a1a24] text-[#00f0ff] border-[#00f0ff]',
    accent: 'border-l-[#00f0ff]',
    neon: '#00f0ff',
  },
};

export default function ClaimCard({ claim }: ClaimProps) {
  const router = useRouter();
  const status = claim.verification?.status || "Unverified";
  const config = statusConfig[status];
  const StatusIcon = config.icon;

  return (
    <article className={`
      group relative p-6 
      bg-[#111118] 
      border-l-4 ${config.accent}
      border-t border-r border-b border-gray-800/50
      hover:border-[${config.neon}]
      transition-all duration-300 
      hover:-translate-y-0.5
      rounded-r-lg
    `}
    style={{
      boxShadow: `0 0 20px ${config.neon}20, inset 0 0 20px ${config.neon}05`,
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.boxShadow = `0 0 30px ${config.neon}40, inset 0 0 30px ${config.neon}10`;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.boxShadow = `0 0 20px ${config.neon}20, inset 0 0 20px ${config.neon}05`;
    }}>
      {/* Grid overlay */}
      <div className="absolute inset-0 opacity-5 pointer-events-none" style={{
        backgroundImage: `
          linear-gradient(${config.neon}40 1px, transparent 1px),
          linear-gradient(90deg, ${config.neon}40 1px, transparent 1px)
        `,
        backgroundSize: '30px 30px'
      }} />
      
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4 relative z-10">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="
            size-11 rounded-lg 
            bg-[#1a1a24] 
            flex items-center justify-center flex-shrink-0
            border-2 border-[#00f0ff]
            group-hover:scale-110 transition-transform duration-300
          "
          style={{
            boxShadow: '0 0 15px rgba(0, 240, 255, 0.5)'
          }}>
            <svg className="size-5 text-[#00f0ff]" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                 style={{ filter: 'drop-shadow(0 0 3px #00f0ff)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-[#00f0ff] truncate font-bold transition-colors"
               style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.5)' }}>
              {claim.source_post?.author || "Desconocido"}
            </p>
            <p className="text-xs text-gray-400 font-medium">{claim.source_post?.platform || "Unknown"}</p>
          </div>
        </div>
        
        <span className={`
          inline-flex items-center gap-1.5 px-3.5 py-1.5 
          rounded-lg text-xs font-bold border-2 
          ${config.badge} 
          group-hover:scale-105 transition-all duration-300
        `}
        style={{
          boxShadow: `0 0 15px ${config.neon}50`
        }}>
          <span style={{ filter: `drop-shadow(0 0 3px ${config.neon})` }}>
            <Icon name={StatusIcon} className="size-4" />
          </span>
          {config.label}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-gray-200 mb-4 line-clamp-2 font-bold text-lg leading-relaxed transition-colors relative z-10"
          style={{ textShadow: '0 0 10px rgba(255, 255, 255, 0.1)' }}>
        "{claim.claim_text}"
      </h3>

      {/* Origin */}
      {claim.original_text !== claim.claim_text && (
        <div className="mb-4 p-4 bg-[#1a1a24] rounded-lg border-2 border-[#00f0ff]/30 relative z-10"
             style={{ boxShadow: '0 0 15px rgba(0, 240, 255, 0.2), inset 0 0 15px rgba(0, 240, 255, 0.05)' }}>
          <p className="text-xs text-[#00f0ff] mb-2 font-bold uppercase tracking-wider"
             style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.5)' }}>ORIGEN</p>
          <p className="text-sm text-gray-300 line-clamp-2 font-medium leading-relaxed">{claim.original_text}</p>
        </div>
      )}

      {/* Analysis */}
      {claim.verification && (
        <>
          <div className="mb-4 p-4 bg-[#1a1a24] rounded-lg border-2 border-[#00f0ff]/30 relative z-10"
               style={{ boxShadow: '0 0 20px rgba(0, 240, 255, 0.2), inset 0 0 20px rgba(0, 240, 255, 0.05)' }}>
            <p className="text-xs text-[#00f0ff] mb-3 font-bold uppercase tracking-wider"
               style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.5)' }}>ANÁLISIS DE FACTCHECKR</p>
            <p className="text-sm text-gray-300 leading-relaxed font-medium">{claim.verification.explanation}</p>
          </div>

          {/* Sources */}
          {claim.verification.sources.length > 0 && (
            <div className="flex flex-wrap items-center gap-2.5 relative z-10">
              <span className="text-xs text-gray-400 font-bold">Fuentes:</span>
              {claim.verification.sources.map((source, index) => {
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
                        text-xs text-[#00f0ff] 
                        bg-[#1a1a24] 
                        hover:bg-[#222230]
                        rounded-lg transition-all duration-200 
                        border-2 border-[#00f0ff]/50 
                        font-semibold
                        hover:scale-105
                      "
                      style={{
                        boxShadow: '0 0 10px rgba(0, 240, 255, 0.3)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.boxShadow = '0 0 15px rgba(0, 240, 255, 0.6)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.boxShadow = '0 0 10px rgba(0, 240, 255, 0.3)';
                      }}
                    >
                      <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                           style={{ filter: 'drop-shadow(0 0 2px #00f0ff)' }}>
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

      {/* Market Signal - Cyberpunk Design */}
      {claim.market && claim.market.status === 'open' && (
        <div className="mt-4 pt-4 border-t border-gray-800 relative z-10">
          <div className="bg-[#1a1a24] rounded-lg p-4 border-2 border-[#00f0ff]/50"
               style={{ boxShadow: '0 0 25px rgba(0, 240, 255, 0.3), inset 0 0 25px rgba(0, 240, 255, 0.05)' }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-[#00f0ff]" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                     style={{ filter: 'drop-shadow(0 0 3px #00f0ff)' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="text-xs font-bold text-[#00f0ff] uppercase tracking-wide"
                      style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.5)' }}>Señal del Mercado</span>
              </div>
              <span className="text-xs text-[#00f0ff]/80 font-medium">
                Lo que piensa la gente informada
              </span>
            </div>
            
            {/* Probability Bar */}
            <div className="mb-3">
              <div className="h-3 bg-[#0a0a0f] rounded-full overflow-hidden border border-[#00f0ff]/30">
                <div className="h-full flex">
                  <div
                    className="bg-gradient-to-r from-[#00ff88] to-[#00f0ff] transition-all duration-500"
                    style={{ 
                      width: `${claim.market.yes_probability * 100}%`,
                      boxShadow: '0 0 10px rgba(0, 255, 136, 0.6)'
                    }}
                  />
                  <div
                    className="bg-gradient-to-r from-[#ff00ff] to-[#ff0066] transition-all duration-500"
                    style={{ 
                      width: `${claim.market.no_probability * 100}%`,
                      boxShadow: '0 0 10px rgba(255, 0, 255, 0.6)'
                    }}
                  />
                </div>
              </div>
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-400">SÍ:</span>
                  <span className="text-base font-bold text-[#00ff88]"
                        style={{ textShadow: '0 0 5px rgba(0, 255, 136, 0.5)' }}>
                    {(claim.market.yes_probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-400">NO:</span>
                  <span className="text-base font-bold text-[#ff00ff]"
                        style={{ textShadow: '0 0 5px rgba(255, 0, 255, 0.5)' }}>
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
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-[#0a0a0f] bg-gradient-to-r from-[#00f0ff] to-[#0066ff] hover:from-[#00ffff] hover:to-[#00f0ff] rounded-lg transition-all duration-300 border-2 border-[#00f0ff]"
              style={{
                boxShadow: '0 0 20px rgba(0, 240, 255, 0.5)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 0 30px rgba(0, 240, 255, 0.8)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = '0 0 20px rgba(0, 240, 255, 0.5)';
              }}
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

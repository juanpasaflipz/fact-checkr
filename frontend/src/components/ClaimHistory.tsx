'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getClaimHistory, removeFromHistory, clearHistory, ClaimHistoryItem } from '@/lib/claimHistory';

export default function ClaimHistory() {
  const router = useRouter();
  const [history, setHistory] = useState<ClaimHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
    // Refresh history every 5 seconds if page is visible
    const interval = setInterval(loadHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadHistory = () => {
    const items = getClaimHistory();
    setHistory(items);
    setLoading(false);
  };

  const handleRemove = (claimId: string) => {
    removeFromHistory(claimId);
    loadHistory();
  };

  const handleClear = () => {
    if (confirm('¿Estás seguro de que quieres borrar todo el historial?')) {
      clearHistory();
      loadHistory();
    }
  };

  const getStatusBadge = (status: ClaimHistoryItem['status']) => {
    const config = {
      Verified: { label: 'Verificado', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
      Debunked: { label: 'Falso', className: 'bg-rose-50 text-rose-700 border-rose-200' },
      Misleading: { label: 'Engañoso', className: 'bg-amber-50 text-amber-700 border-amber-200' },
      Unverified: { label: 'Sin Verificar', className: 'bg-blue-50 text-blue-700 border-blue-200' },
    };
    
    const c = config[status] || config.Unverified;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${c.className}`}>
        {c.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Sin historial</h3>
        <p className="text-gray-600">Las afirmaciones que veas aparecerán aquí</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Historial de Verificaciones</h2>
          <p className="text-gray-600 mt-1">{history.length} {history.length === 1 ? 'verificación' : 'verificaciones'}</p>
        </div>
        <button
          onClick={handleClear}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Limpiar todo
        </button>
      </div>

      <div className="space-y-3">
        {history.map((item) => (
          <div
            key={item.claimId}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  {getStatusBadge(item.status)}
                  <span className="text-xs text-gray-500">
                    {new Date(item.timestamp).toLocaleDateString('es-MX', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <p className="text-gray-900 font-medium line-clamp-2 mb-3">
                  "{item.claimText}"
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      // Navigate to claim detail or search for it
                      router.push(`/?search=${encodeURIComponent(item.claimText)}`);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Ver de nuevo
                  </button>
                </div>
              </div>
              <button
                onClick={() => handleRemove(item.claimId)}
                className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
                title="Eliminar del historial"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


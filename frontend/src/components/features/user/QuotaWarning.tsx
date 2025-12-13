'use client';

import React, { useEffect, useState } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

interface QuotaData {
  tier: string;
  limit: number | null;
  used: number;
  remaining: number | null;
  is_unlimited: boolean;
  is_authenticated: boolean;
}

export default function QuotaWarning() {
  const [quota, setQuota] = useState<QuotaData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchQuota = async () => {
      try {
        const baseUrl = getApiBaseUrl();
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        
        const headers: HeadersInit = {
          'Accept': 'application/json',
        };
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${baseUrl}/api/quota/check`, { headers });
        if (response.ok) {
          const data = await response.json();
          setQuota(data);
        }
      } catch (error) {
        console.error('Error fetching quota:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchQuota();
    // Refresh every 30 seconds
    const interval = setInterval(fetchQuota, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !quota || quota.is_unlimited) {
    return null;
  }

  const remaining = quota.remaining ?? 0;
  const limit = quota.limit ?? 10;
  const percentageUsed = limit > 0 ? ((quota.used / limit) * 100) : 0;
  const isLow = remaining <= 3 && remaining > 0;
  const isExceeded = remaining === 0;

  if (!isLow && !isExceeded) {
    return null; // Only show when low or exceeded
  }

  return (
    <div className={`
      ${isExceeded ? 'bg-rose-50 border-rose-200' : 'bg-amber-50 border-amber-200'}
      border rounded-lg p-4 mb-4
    `}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <div className={`
            ${isExceeded ? 'text-rose-600' : 'text-amber-600'}
            flex-shrink-0 mt-0.5
          `}>
            {isExceeded ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className={`
              ${isExceeded ? 'text-rose-900' : 'text-amber-900'}
              font-semibold text-sm mb-1
            `}>
              {isExceeded ? 'Límite diario alcanzado' : `Solo ${remaining} verificación${remaining !== 1 ? 'es' : ''} restante${remaining !== 1 ? 's' : ''}`}
            </h3>
            <p className={`
              ${isExceeded ? 'text-rose-700' : 'text-amber-700'}
              text-sm
            `}>
              {isExceeded 
                ? 'Has alcanzado tu límite de 10 verificaciones diarias. Actualiza a Pro para verificaciones ilimitadas.'
                : `Has usado ${quota.used} de ${limit} verificaciones hoy. Considera actualizar a Pro para verificaciones ilimitadas.`
              }
            </p>
            <div className="mt-2">
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    isExceeded ? 'bg-rose-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${Math.min(percentageUsed, 100)}%` }}
                />
              </div>
              <div className="flex items-center justify-between mt-1 text-xs">
                <span className={isExceeded ? 'text-rose-600' : 'text-amber-600'}>
                  {quota.used} / {limit}
                </span>
                <span className="text-gray-500">
                  {remaining} restante{remaining !== 1 ? 's' : ''}
                </span>
              </div>
            </div>
          </div>
        </div>
        {isExceeded && (
          <a
            href="/subscription"
            className={`
              ${isExceeded ? 'bg-rose-600 hover:bg-rose-700' : 'bg-amber-600 hover:bg-amber-700'}
              text-white px-4 py-2 rounded-lg text-sm font-semibold
              transition-colors duration-200 whitespace-nowrap
            `}
          >
            Actualizar a Pro
          </a>
        )}
      </div>
    </div>
  );
}


import React from 'react';
import { useRouter } from 'next/navigation';
import { ClaimProps } from './types';

export function MarketSignal({ claim }: ClaimProps) {
    const router = useRouter();

    if (!claim.market || claim.market.status !== 'open') return null;

    return (
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
    );
}

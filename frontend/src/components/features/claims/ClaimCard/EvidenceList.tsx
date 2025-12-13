import React from 'react';
import { ClaimProps } from './types';

export function EvidenceList({ claim }: ClaimProps) {
    if (!claim.verification || claim.verification.sources.length === 0) return null;

    return (
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
    );
}

import React from 'react';
import { ClaimProps } from './types';

export function ClaimBody({ claim }: ClaimProps) {
    return (
        <>
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
        </>
    );
}

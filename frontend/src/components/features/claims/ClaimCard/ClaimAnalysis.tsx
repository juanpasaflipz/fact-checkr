import React, { useState } from 'react';
import { ClaimProps } from './types';

export function ClaimAnalysis({ claim }: ClaimProps) {
    const [readingLevel, setReadingLevel] = useState<'simple' | 'normal' | 'expert'>(() => {
        if (typeof window !== 'undefined') {
            return (localStorage.getItem('reading_level') as 'simple' | 'normal' | 'expert') || 'normal';
        }
        return 'normal';
    });

    if (!claim.verification) return null;

    return (
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
    );
}

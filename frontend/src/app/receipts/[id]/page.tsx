import { Suspense } from 'react';
import { Metadata } from 'next';
import { notFound } from 'next/navigation';

export const metadata: Metadata = {
    title: 'Comprobante de Verificación | FactCheck MX',
    description: 'Detalles de la verificación de información.',
};

async function getClaim(id: string) {
    // Use public API URL or internal
    // For client-side fetch consistency, usually we want to fetch on server
    // But if API_URL is localhost:8000 on server (different from browser)
    // We'll trust NEXT_PUBLIC_API_URL exists.
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

    try {
        const res = await fetch(`${apiUrl}/claims/${id}`, {
            cache: 'no-store', // Always fresh status
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!res.ok) {
            if (res.status === 404) return null;
            throw new Error('Failed to fetch data');
        }

        return res.json();
    } catch (error) {
        console.error("Error fetching claim:", error);
        return null;
    }
}

export default async function ReceiptPage({ params }: { params: { id: string } }) {
    const claim = await getClaim(params.id);

    if (!claim) {
        notFound();
    }

    // Determine Verification Status Styling
    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'verified': return 'bg-green-100 text-green-800 border-green-200';
            case 'mostly_true': return 'bg-green-50 text-green-700 border-green-200';
            case 'mixed': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'misleading': return 'bg-orange-100 text-orange-800 border-orange-200';
            case 'debunked': return 'bg-red-100 text-red-800 border-red-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'verified': return 'Verdadero';
            case 'mostly_true': return 'Mayormente Verdadero';
            case 'mixed': return 'Mixto / Falta Contexto';
            case 'misleading': return 'Engañoso';
            case 'debunked': return 'Falso';
            default: return 'No Verificado';
        }
    };

    const statusColor = getStatusColor(claim.verification.status);
    const statusLabel = getStatusLabel(claim.verification.status);

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100">

                {/* Header */}
                <div className="bg-slate-900 text-white p-6 text-center">
                    <h1 className="text-xl font-bold tracking-tight">FACTCHECK MX</h1>
                    <p className="text-slate-400 text-sm mt-1">Comprobante de Verificación</p>
                </div>

                <div className="p-6 md:p-8 space-y-6">

                    {/* Verdict Banner */}
                    <div className={`flex flex-col items-center justify-center p-6 rounded-lg border-2 ${statusColor} text-center`}>
                        <span className="text-3xl mb-2">
                            {claim.verification.status === 'VERIFIED' ? '✅' :
                                claim.verification.status === 'DEBUNKED' ? '❌' :
                                    claim.verification.status === 'MISLEADING' ? '⚠️' : '⚪️'}
                        </span>
                        <h2 className="text-2xl font-bold uppercase tracking-wide">{statusLabel}</h2>
                        <div className="mt-2 text-sm font-medium opacity-80">
                            Confianza del análisis: {(claim.verification.confidence * 100).toFixed(0)}%
                        </div>
                    </div>

                    {/* Key Facts / Bullets */}
                    {claim.verification.key_evidence_points && claim.verification.key_evidence_points.length > 0 && (
                        <div className="space-y-3">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Puntos Clave</h3>
                            <ul className="space-y-2">
                                {claim.verification.key_evidence_points.map((point: string, idx: number) => (
                                    <li key={idx} className="flex items-start gap-2 text-gray-800">
                                        <span className="text-blue-500 mt-1">•</span>
                                        <span>{point}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Explanation */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Análisis Detallado</h3>
                        <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-100">
                            {claim.verification.explanation}
                        </p>
                    </div>

                    {/* Original Claim */}
                    <div className="pt-4 border-t border-gray-100">
                        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Afirmación Analizada</h3>
                        <blockquote className="text-gray-600 italic border-l-4 border-gray-200 pl-4 py-1 text-sm">
                            "{claim.claim_text}"
                        </blockquote>
                    </div>

                    {/* Sources */}
                    {claim.verification.sources && claim.verification.sources.length > 0 && (
                        <div className="pt-4 border-t border-gray-100">
                            <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Fuentes Consultadas</h3>
                            <ul className="space-y-2 text-sm text-blue-600">
                                {claim.verification.sources.map((source: string, idx: number) => (
                                    <li key={idx}>
                                        <a href={source} target="_blank" rel="noopener noreferrer" className="hover:underline flex items-center gap-1 truncate">
                                            🔗 <span className="truncate">{source}</span>
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="bg-gray-50 p-4 border-t border-gray-100 text-center text-xs text-gray-500">
                    <p>Verificación generada automáticamente por IA + Revisión Humana.</p>
                    <a href="/" className="text-blue-600 hover:underline mt-1 inline-block">Ver más en FactCheck.mx</a>
                </div>

            </div>
        </div>
    );
}

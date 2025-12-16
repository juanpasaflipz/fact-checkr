
import React from "react";

interface BreakingNewsItem {
    id: string;
    text: string;
    source: string;
    time?: string;
}

interface BreakingNewsBannerProps {
    news: BreakingNewsItem[];
}

export default function BreakingNewsBanner({ news }: BreakingNewsBannerProps) {
    if (!news || news.length === 0) return null;

    const item = news[0];

    return (
        <div className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm animate-fade-in-up">
            <div className="flex items-center gap-3 mb-4">
                <div className="flex items-center gap-2 bg-gray-900 border border-gray-900 px-3 py-1.5 rounded-lg">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span className="text-white font-semibold text-sm">NOTICIA DE ÚLTIMA HORA</span>
                </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                    {item.text}
                </h3>
                <p className="text-sm text-gray-600">
                    {item.source} • {item.time ? new Date(item.time).toLocaleTimeString() : "Ahora"} • Verificando ahora...
                </p>
            </div>
        </div>
    );
}

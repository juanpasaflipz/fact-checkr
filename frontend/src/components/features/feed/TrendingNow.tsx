
import React from "react";

interface TrendingItem {
    id: string;
    topic: string;
    claims_count: number;
}

interface TrendingNowProps {
    trends?: TrendingItem[];
}

export default function TrendingNow({ trends }: TrendingNowProps) {
    if (!trends || trends.length === 0) return null;

    return (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm animate-fade-in-up delay-200">
            <div className="px-6 py-5 border-b border-gray-200 bg-white">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                            <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900">Tendiendo Ahora</h2>
                            <p className="text-sm text-gray-600">Las afirmaciones más relevantes en este momento</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 border border-gray-200 rounded-lg">
                        <div className="w-2 h-2 bg-gray-700 rounded-full"></div>
                        <span className="text-xs font-semibold text-gray-700">EN VIVO</span>
                    </div>
                </div>
            </div>
            <div className="divide-y divide-gray-200">
                {trends.map((item, index) => (
                    <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-gray-100 border border-gray-200 rounded-lg flex items-center justify-center text-gray-700 font-semibold text-sm">
                                {index + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="font-semibold text-gray-900 line-clamp-2 mb-1">{item.topic}</p>
                                <div className="flex items-center gap-3 text-xs text-gray-600">
                                    <span>{item.claims_count} menciones</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

import React from "react";
import StatsCard from "@/components/ui/StatsCard";

interface StatsData {
    total_analyzed?: number;
    fake_news_detected?: number;
    verified?: number;
    active_sources?: number;
    trend_percentage?: number;
    trend_up?: boolean;
    recent_24h?: number;
}

interface StatsGridProps {
    stats?: StatsData;
}

export default function StatsGrid({ stats }: StatsGridProps) {
    const statsDisplay = [
        {
            title: "Noticias Analizadas",
            value: stats?.total_analyzed?.toLocaleString("es-MX") || "0",
            trend: stats?.trend_percentage ? `${stats.trend_up ? '+' : ''}${stats.trend_percentage}% vs ayer` : "Sin cambios",
            trendUp: stats?.trend_up ?? true,
            icon: "DocumentSearch" as const,
            color: "blue" as const
        },
        {
            title: "Fake News Detectadas",
            value: stats?.fake_news_detected?.toLocaleString("es-MX") || "0",
            trend: stats?.trend_percentage ? `${stats.trend_up ? '+' : ''}${stats.trend_percentage}% vs ayer` : "Sin cambios",
            trendUp: false,
            icon: "AlertTriangle" as const,
            color: "rose" as const
        },
        {
            title: "Verificadas",
            value: stats?.verified?.toLocaleString("es-MX") || "0",
            trend: stats?.trend_percentage ? `${stats.trend_up ? '+' : ''}${stats.trend_percentage}% vs ayer` : "Sin cambios",
            trendUp: stats?.trend_up ?? true,
            icon: "ShieldCheck" as const,
            color: "emerald" as const
        },
        {
            title: "Fuentes Activas",
            value: stats?.active_sources?.toLocaleString("es-MX") || "0",
            trend: `${stats?.recent_24h || 0} últimas 24h`,
            trendUp: true,
            icon: "Activity" as const,
            color: "amber" as const
        },
    ];

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 animate-fade-in-up">
            {statsDisplay.map((stat, index) => (
                <div key={index} style={{ animationDelay: `${index * 100}ms` }} className="animate-fade-in-up">
                    <StatsCard {...stat} />
                </div>
            ))}
        </div>
    );
}

import { useQuery } from "@tanstack/react-query";
import { getApiBaseUrl } from "@/lib/api-config";
import axios from "axios";

export interface Stats {
    total_analyzed: number;
    fake_news_detected: number;
    verified: number;
    active_sources: number;
    recent_24h: number;
    trend_percentage: number;
    trend_up: boolean;
}

const defaultStats: Stats = {
    total_analyzed: 0,
    fake_news_detected: 0,
    verified: 0,
    active_sources: 0,
    recent_24h: 0,
    trend_percentage: 0,
    trend_up: false
};

const fetchStats = async (): Promise<Stats> => {
    const API_BASE_URL = getApiBaseUrl();
    const response = await axios.get<Stats>(`${API_BASE_URL}/stats`);
    return response.data;
};

export function useStats() {
    return useQuery({
        queryKey: ["stats"],
        queryFn: fetchStats,
        initialData: defaultStats,
        staleTime: 60 * 1000, // 1 minute
        refetchInterval: 60 * 1000, // Refresh every minute
    });
}

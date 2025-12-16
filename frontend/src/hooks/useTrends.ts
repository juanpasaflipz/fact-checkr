import { useQuery } from "@tanstack/react-query";
import { getApiBaseUrl } from "@/lib/api-config";
import axios from "axios";

// Types from original file (approximate)
interface BreakingNewsItem {
    id: string;
    text: string;
    source: string;
    time: string;
}

interface TrendingItem {
    id: string;
    topic: string;
    claims_count: number;
}

const fetchBreakingNews = async (): Promise<BreakingNewsItem[]> => {
    const API_BASE_URL = getApiBaseUrl();
    // Trying to match original endpoint: /claims/trending?limit=5
    const response = await axios.get(`${API_BASE_URL}/claims/trending?limit=5`);
    return response.data.map((c: any) => ({
        id: c.id,
        text: c.claim_text,
        source: c.source_post?.platform || "Twitter",
        time: c.source_post?.timestamp || new Date().toISOString()
    }));
};

const fetchTrendingNow = async (): Promise<TrendingItem[]> => {
    const API_BASE_URL = getApiBaseUrl();
    // Trying to match original endpoint: /trends/topics?limit=5
    const response = await axios.get(`${API_BASE_URL}/trends/topics?limit=5`);
    return response.data.map((t: any) => ({
        id: t.id,
        topic: t.name,
        claims_count: t.claim_count
    }));
};

export function useBreakingNews() {
    return useQuery({
        queryKey: ["breakingNews"],
        queryFn: fetchBreakingNews,
        initialData: [],
        staleTime: 5 * 60 * 1000,
    });
}

export function useTrendingNow() {
    return useQuery({
        queryKey: ["trendingNow"],
        queryFn: fetchTrendingNow,
        initialData: [],
        staleTime: 10 * 60 * 1000,
    });
}

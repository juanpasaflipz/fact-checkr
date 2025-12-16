import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import { getApiBaseUrl } from "@/lib/api-config";
import axios from "axios";

// Define Claim type matching the one in page.tsx
export interface Claim {
    id: string;
    claim_text: string;
    original_text: string;
    verification: {
        status: "Verified" | "Debunked" | "Misleading" | "Unverified";
        explanation: string;
        sources: string[];
        evidence_details?: Array<{
            source: string;
            url: string;
            snippet: string;
        }>;
    };
    market?: {
        id: number;
        slug: string;
        question: string;
        yes_probability: number;
        no_probability: number;
        volume: number;
        closes_at: string;
        status: string;
        claim_id: string;
        category: string;
    };
    explanation: string;
    sources: string[];
    source_post: {
        platform: string;
        author: string;
        url: string;
        timestamp: string;
    } | null;
    platform: string;
    author: string;
    url: string;
    timestamp: string;
}

const fetchClaims = async ({ pageParam = 0, query = "", status = "" }) => {
    const API_BASE_URL = getApiBaseUrl();
    const limit = 20;

    let url = "";
    let params: any = { skip: pageParam, limit };

    if (query) {
        url = `${API_BASE_URL}/claims/search`;
        params = { query }; // Search usually returns all results or limited by backend, not paginated the same way in original code?
        // Looking at original code:
        // if (query) url = `${API_BASE_URL}/claims/search?query=${encodeURIComponent(query)}`;
        // else url = `${API_BASE_URL}/claims?skip=${skip}&limit=${limit}`;
    } else {
        url = `${API_BASE_URL}/claims`;
        if (status && status !== "todos") {
            params.status = status;
        }
    }

    const response = await axios.get<Claim[]>(url, { params });
    return response.data;
};

export function useClaims(query: string = "", status: string = "") {
    return useInfiniteQuery({
        queryKey: ["claims", query, status],
        queryFn: ({ pageParam = 0 }: { pageParam: number }) => fetchClaims({ pageParam, query, status }),
        initialPageParam: 0,
        getNextPageParam: (lastPage, allPages) => {
            // If less items than limit were returned, we are done
            if (lastPage.length < 20) return undefined;
            // Otherwise next offset is current count of items
            return allPages.length * 20;
        },
        // Only fetch if query is valid or empty (always valid)
        enabled: true,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

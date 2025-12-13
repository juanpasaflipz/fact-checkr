export type VerificationStatus = "Verified" | "Debunked" | "Misleading" | "Unverified";

export interface EvidenceDetail {
    url: string;
    snippet?: string;
    timestamp?: string | null;
    relevance_score?: number | null;
    title?: string | null;
    domain?: string | null;
}

export interface ClaimProps {
    claim: {
        id: string;
        claim_text: string;
        original_text: string;
        verification: {
            status: VerificationStatus;
            explanation: string;
            sources: string[];
            evidence_details?: EvidenceDetail[];
        } | null;
        source_post: {
            platform: string;
            author: string;
            url: string;
            timestamp: string;
        } | null;
        market?: {
            id: number;
            slug: string;
            question: string;
            yes_probability: number;
            no_probability: number;
            volume: number;
            closes_at: string | null;
            status: string;
            claim_id: string | null;
        } | null;
    };
}

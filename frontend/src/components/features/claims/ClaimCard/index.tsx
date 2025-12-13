import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { addToHistory } from '@/lib/claimHistory';
import { getApiBaseUrl } from '@/lib/api-config';
import { ClaimProps } from './types';
import { statusConfig } from './config';
import { ClaimHeader } from './ClaimHeader';
import { ClaimBody } from './ClaimBody';
import { ClaimAnalysis } from './ClaimAnalysis';
import { EvidenceList } from './EvidenceList';
import { MarketSignal } from './MarketSignal';

export default function ClaimCard({ claim }: ClaimProps) {
    const router = useRouter();
    const status = claim.verification?.status || "Unverified";
    const config = statusConfig[status];
    const [sharing, setSharing] = useState(false);
    const [shareSuccess, setShareSuccess] = useState(false);

    // Add claim to history when component mounts (when claim is viewed)
    useEffect(() => {
        addToHistory({
            id: claim.id,
            claim_text: claim.claim_text,
            verification: claim.verification,
        });
    }, [claim.id, claim.claim_text, claim.verification]);

    const handleShare = async (type: 'tweet' | 'image') => {
        if (type === 'tweet') {
            setSharing(true);
            try {
                const baseUrl = getApiBaseUrl();
                const response = await fetch(`${baseUrl}/api/share/claim/${claim.id}`, {
                    headers: { 'Accept': 'application/json' }
                });

                if (response.ok) {
                    const data = await response.json();

                    // Copy to clipboard
                    if (navigator.clipboard) {
                        await navigator.clipboard.writeText(data.tweet_text);
                        setShareSuccess(true);
                        setTimeout(() => setShareSuccess(false), 2000);
                    } else {
                        // Fallback for older browsers
                        const textArea = document.createElement('textarea');
                        textArea.value = data.tweet_text;
                        document.body.appendChild(textArea);
                        textArea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textArea);
                        setShareSuccess(true);
                        setTimeout(() => setShareSuccess(false), 2000);
                    }
                }
            } catch (error) {
                console.error('Error sharing:', error);
            } finally {
                setSharing(false);
            }
        } else if (type === 'image') {
            // For image sharing, we'll create a simple canvas-based image
            // This is a simplified version - in production you'd want server-side image generation
            alert('Compartir como imagen próximamente. Por ahora usa "Copiar para Tweet".');
        }
    };

    return (
        <article className={`
      group relative p-6 
      bg-white 
      border-l-4 ${config.accent}
      border-t border-r border-b border-gray-200
      transition-all duration-200 
      hover:shadow-md hover:border-gray-300
      rounded-lg
    `}>
            <ClaimHeader claim={claim} />
            <ClaimBody claim={claim} />
            {claim.verification && (
                <>
                    <ClaimAnalysis claim={claim} />
                    <EvidenceList claim={claim} />
                </>
            )}
            <MarketSignal claim={claim} />
        </article>
    );
}

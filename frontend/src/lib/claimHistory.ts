/**
 * Utility functions for managing claim history in localStorage
 */

export interface ClaimHistoryItem {
  claimId: string;
  claimText: string;
  timestamp: string;
  status: 'Verified' | 'Debunked' | 'Misleading' | 'Unverified';
  claimUrl?: string;
}

const HISTORY_KEY = 'factcheckr_claim_history';
const MAX_HISTORY_ITEMS = 50; // Keep last 50 claims

/**
 * Get all claim history items
 */
export function getClaimHistory(): ClaimHistoryItem[] {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    if (!stored) {
      return [];
    }
    return JSON.parse(stored);
  } catch (error) {
    console.error('Error reading claim history:', error);
    return [];
  }
}

/**
 * Add a claim to history
 */
export function addToHistory(claim: {
  id: string;
  claim_text: string;
  verification?: { status: string } | null;
}): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    const history = getClaimHistory();
    
    // Remove if already exists (to avoid duplicates)
    const filtered = history.filter(item => item.claimId !== claim.id);
    
    // Add new item at the beginning
    const newItem: ClaimHistoryItem = {
      claimId: claim.id,
      claimText: claim.claim_text,
      timestamp: new Date().toISOString(),
      status: (claim.verification?.status as ClaimHistoryItem['status']) || 'Unverified',
    };
    
    const updated = [newItem, ...filtered].slice(0, MAX_HISTORY_ITEMS);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error('Error saving claim to history:', error);
  }
}

/**
 * Remove a claim from history
 */
export function removeFromHistory(claimId: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    const history = getClaimHistory();
    const filtered = history.filter(item => item.claimId !== claimId);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Error removing claim from history:', error);
  }
}

/**
 * Clear all history
 */
export function clearHistory(): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch (error) {
    console.error('Error clearing history:', error);
  }
}

/**
 * Get history count
 */
export function getHistoryCount(): number {
  return getClaimHistory().length;
}


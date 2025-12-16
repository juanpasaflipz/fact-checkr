import { render, screen } from '@testing-library/react';
import ClaimCard from '../ClaimCard';
import { describe, it, expect, vi } from 'vitest';

vi.mock('next/navigation', () => ({
    useRouter: () => ({
        push: vi.fn(),
        replace: vi.fn(),
        prefetch: vi.fn(),
        back: vi.fn(),
    }),
}));

// Mock types since we might not have access to the exact type definition file easily here
// or we can import if available. Assuming relative import works.

const mockClaim = {
    id: '123',
    claim_text: 'Sky is green',
    original_text: 'Look at the sky, it is green!',
    verification: {
        status: 'Debunked',
        explanation: 'Sky is actually blue.',
        sources: ['Science Daily'],
    },
    source_post: {
        platform: 'Twitter',
        author: 'User123',
        url: 'http://twitter.com/123',
        timestamp: '2023-01-01T12:00:00Z',
    },
    explanation: 'Sky is actually blue.',
    sources: ['Science Daily'],
    platform: 'Twitter',
    author: 'User123',
    url: 'http://twitter.com/123',
    timestamp: '2023-01-01T12:00:00Z',
};

describe('ClaimCard', () => {
    it('renders claim text correctly', () => {
        render(<ClaimCard claim={mockClaim as any} />);
        expect(screen.getByText('"Sky is green"')).toBeInTheDocument();
    });

    it('renders verification status', () => {
        render(<ClaimCard claim={mockClaim as any} />);
        expect(screen.getByText('Falso')).toBeInTheDocument(); // Assuming 'Debunked' maps to 'Falso' in UI
    });

    it('renders explanation', () => {
        render(<ClaimCard claim={mockClaim as any} />);
        expect(screen.getByText('Sky is actually blue.')).toBeInTheDocument();
    });

    it('renders source information', () => {
        render(<ClaimCard claim={mockClaim as any} />);
        expect(screen.getByText('User123')).toBeInTheDocument();
        expect(screen.getByText('Twitter')).toBeInTheDocument();
    });
});

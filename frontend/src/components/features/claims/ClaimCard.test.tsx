import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ClaimCard from './ClaimCard'

// Mock useRouter
vi.mock('next/navigation', () => ({
    useRouter: () => ({
        push: vi.fn(),
    }),
}))

// Mock libs
vi.mock('@/lib/claimHistory', () => ({
    addToHistory: vi.fn(),
}))

vi.mock('@/lib/api-config', () => ({
    getApiBaseUrl: () => 'http://localhost:8000',
}))

describe('ClaimCard', () => {
    const mockClaimWithVerification = {
        id: '1',
        claim_text: 'Test Claim',
        original_text: 'Test Claim',
        verification: {
            status: 'Verified' as const,
            explanation: 'Verified explanation',
            sources: ['https://example.com'],
            evidence_details: [],
        },
        source_post: {
            platform: 'Twitter',
            author: 'TestUser',
            url: 'https://twitter.com/test',
            timestamp: '2023-01-01',
        },
        market: null,
    }

    const mockClaimUnverified = {
        ...mockClaimWithVerification,
        verification: null,
    }

    it('renders claim text', () => {
        render(<ClaimCard claim={mockClaimWithVerification} />)
        expect(screen.getByText('"Test Claim"')).toBeInTheDocument()
    })

    it('renders verification status', () => {
        render(<ClaimCard claim={mockClaimWithVerification} />)
        expect(screen.getByText('Verificado')).toBeInTheDocument()
    })

    it('renders explanation for verified claim', () => {
        render(<ClaimCard claim={mockClaimWithVerification} />)
        expect(screen.getByText('Verified explanation')).toBeInTheDocument()
    })

    it('renders unverified status when verification is null', () => {
        render(<ClaimCard claim={mockClaimUnverified} />)
        expect(screen.getByText('Sin Verificar')).toBeInTheDocument()
    })
})

import { render, screen } from '@testing-library/react';
import Home from '../page';
import { describe, it, expect, vi } from 'vitest';

// Mock the cutsom hooks
vi.mock('@/hooks/useClaims', () => ({
    useClaims: () => ({
        data: { pages: [] },
        fetchNextPage: vi.fn(),
        hasNextPage: false,
        isFetchingNextPage: false,
        isLoading: false,
        isError: false,
        error: null,
    }),
}));

vi.mock('@/hooks/useStats', () => ({
    useStats: () => ({
        data: {
            total_analyzed: 100,
            fake_news_detected: 10,
            verified: 50,
            active_sources: 5,
            recent_24h: 12,
            trend_percentage: 5,
            trend_up: true,
        },
    }),
}));

vi.mock('@/hooks/useTrends', () => ({
    useBreakingNews: () => ({ data: [] }),
    useTrendingNow: () => ({ data: [] }),
}));

// Mock simple components to avoid complex rendering
vi.mock('@/components/features/layout/Sidebar', () => ({
    default: () => <div data-testid="sidebar">Sidebar</div>,
}));

vi.mock('@/components/features/layout/Header', () => ({
    default: () => <div data-testid="header">Header</div>,
}));

vi.mock('@/components/ui/StatsCard', () => ({
    default: ({ title, value }: any) => <div data-testid="stats-card">{title}: {value}</div>,
}));

describe('Home Page', () => {
    it('renders layout components', () => {
        render(<Home />);
        expect(screen.getByTestId('sidebar')).toBeInTheDocument();
        expect(screen.getByTestId('header')).toBeInTheDocument();
    });

    it('renders stats', () => {
        render(<Home />);
        // Check if stats from mock are passed to cards
        expect(screen.getByText('Noticias Analizadas: 100')).toBeInTheDocument();
        expect(screen.getByText('Fake News Detectadas: 10')).toBeInTheDocument();
    });
});

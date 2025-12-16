"use client";

import { useState, useEffect } from "react";
import ClaimCard from "@/components/features/claims/ClaimCard";
import Sidebar from "@/components/features/layout/Sidebar";
import Header from "@/components/features/layout/Header";
import OnboardingModal from "@/components/features/user/OnboardingModal";
import TrendingTopics from "@/components/features/topics/TrendingTopics";
import QuotaWarning from "@/components/features/user/QuotaWarning";

// Refactored components
import BreakingNewsBanner from "@/components/features/feed/BreakingNewsBanner";
import StatsGrid from "@/components/features/feed/StatsGrid";
import TrendingNow from "@/components/features/feed/TrendingNow";
import FeedTabs from "@/components/features/feed/FeedTabs";

// Hooks
import { useClaims } from "@/hooks/useClaims";
import { useStats } from "@/hooks/useStats";
import { useBreakingNews, useTrendingNow } from "@/hooks/useTrends";
import { useOnboarding } from "@/hooks/useOnboarding";
import { useInView } from "react-intersection-observer";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("todos");

  // New Hook for onboarding
  const { data: user, isOnboardingCompleted } = useOnboarding();
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Sync basic state for modal visibility
  useEffect(() => {
    if (isOnboardingCompleted === false) {
      setShowOnboarding(true);
    }
  }, [isOnboardingCompleted]);

  // Map frontend tabs to backend status
  const statusMap: { [key: string]: string } = {
    todos: "",
    verificados: "verified",
    falsos: "debunked",
    "sin-verificar": "unverified",
  };

  const statusFilter = statusMap[activeTab] || "";

  // React Query Hooks
  const {
    data: claimsData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: isClaimsLoading,
    isError: isClaimsError,
    error: claimsError,
    refetch: refetchClaims
  } = useClaims(searchQuery, statusFilter);

  const { data: statsData } = useStats();
  const { data: breakingNews } = useBreakingNews();
  const { data: trendingNow } = useTrendingNow();

  // Infinite Scroll Trigger
  const { ref, inView } = useInView();

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  // Flatten claims pages
  const claims = claimsData?.pages.flatMap((page) => page) || [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search is handled reactively by valid query key in hook
  };

  const handleRetry = () => {
    refetchClaims();
  };

  return (
    <div className="min-h-screen bg-gray-50 relative">
      {showOnboarding && (
        <OnboardingModal
          onComplete={() => {
            setShowOnboarding(false);
            // In a real app we would call mutation here to update backend
          }}
        />
      )}
      <Sidebar />
      <div className="lg:pl-64 relative z-10">
        <Header
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onSearch={handleSearch}
        />
        <main className="p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-8">
            <QuotaWarning />

            <BreakingNewsBanner news={breakingNews || []} />

            <StatsGrid stats={statsData} />

            <TrendingNow trends={trendingNow} />

            <div className="mb-6">
              <TrendingTopics />
            </div>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
              <div className="px-6 py-6 border-b border-gray-200 bg-white">
                <h2 className="text-gray-900 mb-5 text-xl font-semibold">
                  Feed de Verificación
                </h2>

                <FeedTabs
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                />
              </div>

              {/* Error State */}
              {isClaimsError && (
                <div className="p-6 text-center">
                  <div className="bg-red-50 text-red-800 p-4 rounded-lg mb-4">
                    <p className="font-medium">Error al cargar datos</p>
                    <p className="text-sm mt-1">{(claimsError as Error)?.message || "Ocurrió un error inesperado"}</p>
                  </div>
                  <button
                    onClick={handleRetry}
                    className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    Reintentar
                  </button>
                </div>
              )}

              {/* Loading State (Initial) */}
              {isClaimsLoading && (
                <div className="divide-y divide-gray-100">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="p-6 animate-pulse">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              )}

              {/* Claims List */}
              <div className="divide-y divide-gray-100">
                {claims.map((claim) => (
                  <ClaimCard key={claim.id} claim={claim} />
                ))}

                {/* Empty State */}
                {!isClaimsLoading && !isClaimsError && claims.length === 0 && (
                  <div className="p-12 text-center text-gray-500">
                    <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-lg font-medium text-gray-900">No se encontraron resultados</p>
                    <p className="text-sm mt-1">Intenta ajustar tus filtros de búsqueda</p>
                  </div>
                )}
              </div>

              {/* Infinite Scroll Loader */}
              {(hasNextPage || isFetchingNextPage) && (
                <div ref={ref} className="p-8 flex justify-center">
                  <div className="w-8 h-8 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

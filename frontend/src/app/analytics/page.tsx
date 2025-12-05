'use client';

import { useState } from 'react';
import TopicDistributionChart from '@/components/charts/TopicDistributionChart';
import PlatformDistributionChart from '@/components/charts/PlatformDistributionChart';
import EngagementMetricsChart from '@/components/charts/EngagementMetricsChart';
import DailyActivityChart from '@/components/charts/DailyActivityChart';
import TopicComparisonChart from '@/components/charts/TopicComparisonChart';
import AudienceStatsChart from '@/components/charts/AudienceStatsChart';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const [selectedTopics, setSelectedTopics] = useState<number[]>([]);
  const [activeSection, setActiveSection] = useState<'overview' | 'topics' | 'platforms' | 'engagement' | 'audience' | 'comparison'>('overview');

  const timePeriods = [
    { label: '7 días', value: 7 },
    { label: '30 días', value: 30 },
    { label: '90 días', value: 90 },
    { label: '365 días', value: 365 }
  ];

  const sections = [
    { id: 'overview', label: 'Resumen', icon: '📊' },
    { id: 'topics', label: 'Temas', icon: '🏷️' },
    { id: 'platforms', label: 'Plataformas', icon: '📱' },
    { id: 'engagement', label: 'Engagement', icon: '💬' },
    { id: 'audience', label: 'Audiencia', icon: '👥' },
    { id: 'comparison', label: 'Comparación', icon: '⚖️' }
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0f] relative">
      {/* Animated scan line effect */}
      <div className="fixed inset-0 pointer-events-none z-0 opacity-5">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#00f0ff] to-transparent animate-scan-line"></div>
      </div>

      <Sidebar />
      <div className="lg:pl-64 relative z-10">
        <Header 
          searchQuery="" 
          setSearchQuery={() => {}} 
          onSearch={() => {}} 
        />
        <main className="p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Page Header */}
            <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
                 style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-bold text-[#00f0ff] mb-2"
                      style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
                    Dashboard de Analytics
                  </h1>
                  <p className="text-gray-400">
                    Visualización completa de datos y métricas de fact-checking
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex gap-2 bg-[#1a1a24] rounded-lg p-1 border border-[#00f0ff]/20">
                    {timePeriods.map((period) => (
                      <button
                        key={period.value}
                        onClick={() => setDays(period.value)}
                        className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                          days === period.value
                            ? 'bg-[#00f0ff] text-[#0a0a0f]'
                            : 'text-gray-400 hover:text-[#00f0ff]'
                        }`}
                      >
                        {period.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-4"
                 style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
              <div className="flex flex-wrap gap-2">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id as any)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${
                      activeSection === section.id
                        ? 'bg-[#00f0ff] text-[#0a0a0f]'
                        : 'bg-[#1a1a24] text-gray-400 border border-gray-700 hover:border-[#00f0ff]/30 hover:text-[#00f0ff]'
                    }`}
                  >
                    <span>{section.icon}</span>
                    <span>{section.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Content Sections */}
            {activeSection === 'overview' && (
              <div className="space-y-6">
                <DailyActivityChart days={days} />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <TopicDistributionChart days={days} />
                  <PlatformDistributionChart days={days} />
                </div>
                <EngagementMetricsChart days={days} />
              </div>
            )}

            {activeSection === 'topics' && (
              <div className="space-y-6">
                <TopicDistributionChart days={days} />
              </div>
            )}

            {activeSection === 'platforms' && (
              <div className="space-y-6">
                <PlatformDistributionChart days={days} />
              </div>
            )}

            {activeSection === 'engagement' && (
              <div className="space-y-6">
                <EngagementMetricsChart days={days} />
              </div>
            )}

            {activeSection === 'audience' && (
              <div className="space-y-6">
                <AudienceStatsChart days={days} />
              </div>
            )}

            {activeSection === 'comparison' && (
              <div className="space-y-6">
                <div className="bg-[#111118] rounded-lg border-2 border-[#00f0ff]/30 p-6"
                     style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
                  <h3 className="text-xl font-bold text-[#00f0ff] mb-4"
                      style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
                    Comparación de Temas
                  </h3>
                  <p className="text-gray-400 mb-4">
                    Selecciona temas para comparar (máximo 5)
                  </p>
                  <div className="bg-[#1a1a24] rounded-lg p-4 border border-[#00f0ff]/20">
                    <p className="text-sm text-gray-400 mb-2">
                      IDs de temas seleccionados: {selectedTopics.length > 0 ? selectedTopics.join(', ') : 'Ninguno'}
                    </p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Ingresa IDs de temas separados por comas (ej: 1,2,3)"
                        className="flex-1 bg-[#0a0a0f] border-2 border-[#00f0ff]/30 rounded-lg px-4 py-2 text-[#00f0ff] focus:border-[#00f0ff] focus:outline-none"
                        onChange={(e) => {
                          const ids = e.target.value
                            .split(',')
                            .map(id => parseInt(id.trim()))
                            .filter(id => !isNaN(id) && id > 0)
                            .slice(0, 5);
                          setSelectedTopics(ids);
                        }}
                      />
                    </div>
                  </div>
                </div>
                {selectedTopics.length > 0 && (
                  <TopicComparisonChart topicIds={selectedTopics} days={days} />
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}


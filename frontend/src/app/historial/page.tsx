'use client';

import React from 'react';
import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';
import ClaimHistory from '@/components/ClaimHistory';

export default function HistorialPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-64 relative z-10">
        <Header />
        <main className="p-6 lg:p-8">
          <div className="max-w-4xl mx-auto">
            <ClaimHistory />
          </div>
        </main>
      </div>
    </div>
  );
}


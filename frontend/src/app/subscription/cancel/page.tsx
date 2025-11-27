'use client';

import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export default function SubscriptionCancelPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="lg:pl-64">
        <Header 
          searchQuery="" 
          setSearchQuery={() => {}} 
          onSearch={(e) => e.preventDefault()} 
        />
        
        <main className="p-6 lg:p-8">
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 text-center">
              <div className="mx-auto mb-6 w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Payment Cancelled
              </h1>
              <p className="text-lg text-gray-600 mb-8">
                Your subscription was not processed
              </p>

              <div className="mb-8">
                <p className="text-gray-700 mb-4">
                  No charges were made to your account. You can try again anytime.
                </p>
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => router.push('/subscription')}
                  className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transition-all"
                >
                  Try Again
                </button>
                <button
                  onClick={() => router.push('/')}
                  className="w-full bg-white border-2 border-gray-300 text-gray-700 py-3 px-6 rounded-lg font-semibold hover:border-gray-400 transition-all"
                >
                  Return to Dashboard
                </button>
              </div>

              <div className="mt-8 pt-6 border-t border-gray-200 text-sm text-gray-600">
                <p>
                  Need help? Contact{' '}
                  <a href="mailto:support@factcheck.mx" className="text-blue-600 hover:underline">
                    support@factcheck.mx
                  </a>
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}


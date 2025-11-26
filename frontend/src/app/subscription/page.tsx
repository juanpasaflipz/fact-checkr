'use client';

import { useState } from 'react';
import { redirectToCheckout } from '@/lib/stripe';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export default function SubscriptionPage() {
  const [billingCycle, setBillingCycle] = useState<'month' | 'year'>('month');
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (tier: 'pro' | 'team', trialDays: number = 7) => {
    setLoading(tier);
    setError(null);
    
    try {
      await redirectToCheckout(tier, billingCycle, trialDays);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start checkout');
      setLoading(null);
    }
  };

  const pricingTiers = [
    {
      name: 'Free',
      price: { month: 0, year: 0 },
      description: 'Perfect for casual users',
      features: [
        '10 manual verifications/month',
        '100 API requests/day',
        '50 search queries/day',
        'Last 7 days of data only',
        'Basic analytics',
        'No exports',
        'No API access',
        'No alerts',
      ],
      cta: 'Current Plan',
      disabled: true,
      highlight: false,
    },
    {
      name: 'Pro',
      price: { month: 19, year: 190 },
      description: 'Perfect for journalists, researchers, content creators',
      features: [
        'Unlimited manual verifications',
        '10,000 API requests/day',
        'Unlimited search queries',
        'Full historical data access (all-time)',
        'Advanced analytics (365 days)',
        'Unlimited exports (CSV, JSON, Excel, PDF)',
        'Custom alerts (5 active alerts)',
        'Priority processing (2x faster)',
        'API access (RESTful API)',
        'Save collections (up to 10)',
        'Bulk verification',
        '24-hour email support',
      ],
      cta: 'Start 7-Day Free Trial',
      disabled: false,
      highlight: true,
      savings: { month: 0, year: 38 },
    },
    {
      name: 'Team',
      price: { month: 79, year: 790 },
      description: 'Perfect for small newsrooms, NGOs (2-10 users)',
      features: [
        'Everything in Pro, plus:',
        'Up to 10 team members',
        'Shared collections and dashboards',
        'Team activity logs',
        'Role-based permissions',
        '50,000 API requests/day',
        '20 active alerts',
        'Priority email support (12-hour response)',
        'Custom branding options',
      ],
      cta: 'Subscribe to Team',
      disabled: false,
      highlight: false,
      savings: { month: 0, year: 158 },
    },
  ];

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
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Choose Your Plan
              </h1>
              <p className="text-lg text-gray-600 mb-6">
                Select the perfect plan for your fact-checking needs
              </p>
              
              {/* Billing Toggle */}
              <div className="inline-flex items-center bg-white rounded-lg p-1 shadow-sm border border-gray-200">
                <button
                  onClick={() => setBillingCycle('month')}
                  className={`px-6 py-2 rounded-md font-medium transition-all ${
                    billingCycle === 'month'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Monthly
                </button>
                <button
                  onClick={() => setBillingCycle('year')}
                  className={`px-6 py-2 rounded-md font-medium transition-all relative ${
                    billingCycle === 'year'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Annual
                  <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
                    Save 17%
                  </span>
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="max-w-4xl mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            {/* Pricing Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
              {pricingTiers.map((tier) => {
                const price = tier.price[billingCycle];
                const savings = tier.savings?.[billingCycle] || 0;
                const isPro = tier.name === 'Pro';
                const isTeam = tier.name === 'Team';
                
                return (
                  <div
                    key={tier.name}
                    className={`relative bg-white rounded-xl shadow-lg border-2 transition-all ${
                      tier.highlight
                        ? 'border-blue-500 scale-105 shadow-2xl'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {/* Most Popular Badge */}
                    {tier.highlight && (
                      <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                        <span className="bg-gradient-to-r from-blue-600 to-blue-700 text-white text-sm font-semibold px-4 py-1 rounded-full shadow-lg">
                          Most Popular
                        </span>
                      </div>
                    )}

                    <div className="p-8">
                      {/* Tier Name */}
                      <h3 className="text-2xl font-bold text-gray-900 mb-2">
                        {tier.name}
                      </h3>
                      <p className="text-gray-600 text-sm mb-6">{tier.description}</p>

                      {/* Price */}
                      <div className="mb-6">
                        <div className="flex items-baseline">
                          <span className="text-5xl font-bold text-gray-900">
                            ${price}
                          </span>
                          <span className="text-gray-600 ml-2">
                            /{billingCycle === 'month' ? 'month' : 'year'}
                          </span>
                        </div>
                        {billingCycle === 'year' && savings > 0 && (
                          <p className="text-sm text-green-600 font-medium mt-2">
                            💰 Save ${savings}/year (17% discount)
                          </p>
                        )}
                      </div>

                      {/* Features */}
                      <ul className="space-y-3 mb-8">
                        {tier.features.map((feature, idx) => (
                          <li key={idx} className="flex items-start">
                            <span className="text-green-500 mr-2 mt-1">✅</span>
                            <span className="text-gray-700 text-sm">{feature}</span>
                          </li>
                        ))}
                      </ul>

                      {/* CTA Button */}
                      <button
                        onClick={() => {
                          if (isPro) handleSubscribe('pro', 7);
                          else if (isTeam) handleSubscribe('team', 0);
                        }}
                        disabled={tier.disabled || loading !== null}
                        className={`w-full py-3 px-6 rounded-lg font-semibold transition-all ${
                          tier.disabled
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : tier.highlight
                            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl'
                            : 'bg-gray-900 text-white hover:bg-gray-800'
                        } ${
                          loading === tier.name.toLowerCase() ? 'opacity-50 cursor-wait' : ''
                        }`}
                      >
                        {loading === tier.name.toLowerCase() ? (
                          <span className="flex items-center justify-center">
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Processing...
                          </span>
                        ) : (
                          tier.cta
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Trust Indicators */}
            <div className="text-center space-y-4">
              <p className="text-gray-600">
                <span className="font-semibold">30-day money-back guarantee</span> • 
                Cancel anytime from your account settings
              </p>
              <p className="text-sm text-gray-500">
                Secure payment powered by Stripe
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}


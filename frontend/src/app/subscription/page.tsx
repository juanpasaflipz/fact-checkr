'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { redirectToCheckout } from '@/lib/stripe';
import { useAuth } from '@/contexts/AuthContext';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export default function SubscriptionPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [billingCycle, setBillingCycle] = useState<'month' | 'year'>('month');
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Redirect to signin if not authenticated
    if (!authLoading && !isAuthenticated) {
      router.push('/signin?redirect=/subscription');
    }
  }, [isAuthenticated, authLoading, router]);

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  const handleSubscribe = async (tier: 'pro' | 'team', trialDays: number = 7) => {
    setLoading(tier);
    setError(null);
    
    try {
      await redirectToCheckout(tier, billingCycle, trialDays);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al iniciar el pago');
      setLoading(null);
    }
  };

  const pricingTiers = [
    {
      name: 'Gratis',
      price: { month: 0, year: 0 },
      description: 'Perfecto para usuarios casuales',
      features: [
        '10 verificaciones diarias',
        '100 solicitudes API/día',
        '50 búsquedas/día',
        'Solo últimos 7 días de datos',
        'Analíticas básicas',
        'Sin exportaciones',
        'Sin acceso API',
        'Sin alertas',
      ],
      cta: 'Plan Actual',
      disabled: true,
      highlight: false,
    },
    {
      name: 'Pro',
      price: { month: 199, year: 1900 },
      description: 'Perfecto para periodistas, investigadores, creadores de contenido',
      features: [
        'Verificaciones manuales ilimitadas',
        '10,000 solicitudes API/día',
        'Búsquedas ilimitadas',
        'Acceso completo a datos históricos (todo el tiempo)',
        'Analíticas avanzadas (365 días)',
        'Exportaciones ilimitadas (CSV, JSON, Excel, PDF)',
        'Alertas personalizadas (5 alertas activas)',
        'Procesamiento prioritario (2x más rápido)',
        'Acceso API (API RESTful)',
        'Guardar colecciones (hasta 10)',
        'Verificación masiva',
        'Soporte por email 24 horas',
      ],
      cta: 'Iniciar Prueba Gratuita de 7 Días',
      disabled: false,
      highlight: true,
      savings: { month: 0, year: 488 }, // 199 * 12 = 2388, savings = 2388 - 1900 = 488
    },
    {
      name: 'Equipo',
      price: { month: 1399, year: 11000 },
      description: 'Perfecto para redacciones pequeñas, ONGs (2-10 usuarios)',
      features: [
        'Todo lo de Pro, más:',
        'Hasta 10 miembros del equipo',
        'Colecciones y dashboards compartidos',
        'Registros de actividad del equipo',
        'Permisos basados en roles',
        '50,000 solicitudes API/día',
        '20 alertas activas',
        'Soporte prioritario por email (respuesta en 12 horas)',
        'Opciones de marca personalizada',
      ],
      cta: 'Suscribirse a Equipo',
      disabled: false,
      highlight: false,
      savings: { month: 0, year: 5788 }, // 1399 * 12 = 16788, savings = 16788 - 11000 = 5788
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
                Elige Tu Plan
              </h1>
              <p className="text-lg text-gray-600 mb-6">
                Selecciona el plan perfecto para tus necesidades de verificación
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
                  Mensual
                </button>
                <button
                  onClick={() => setBillingCycle('year')}
                  className={`px-6 py-2 rounded-md font-medium transition-all relative ${
                    billingCycle === 'year'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Anual
                  <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
                    Ahorra 17%
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
                          Más Popular
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
                            ${price.toLocaleString('es-MX')}
                          </span>
                          <span className="text-gray-600 ml-2">
                            MXN /{billingCycle === 'month' ? 'mes' : 'año'}
                          </span>
                        </div>
                        {billingCycle === 'year' && savings > 0 && (
                          <p className="text-sm text-green-600 font-medium mt-2">
                            💰 Ahorra ${savings.toLocaleString('es-MX')} MXN/año ({Math.round((savings / (price * 12)) * 100)}% de descuento)
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
                            Procesando...
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
                <span className="font-semibold">Garantía de devolución de 30 días</span> • 
                Cancela en cualquier momento desde la configuración de tu cuenta
              </p>
              <p className="text-sm text-gray-500">
                Pago seguro con Stripe
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}


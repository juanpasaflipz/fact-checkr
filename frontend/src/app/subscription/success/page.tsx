'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';

function SubscriptionSuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [subscriptionInfo, setSubscriptionInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    // In a real implementation, you'd fetch subscription details from your backend
    // using the session_id to verify the payment
    if (sessionId) {
      // Simulate fetching subscription info
      // TODO: Replace with actual API call to fetch subscription details
      setTimeout(() => {
        setSubscriptionInfo({
          plan: 'Pro',
          billing: 'Monthly',
          amount: '$199.00 MXN', // Will be fetched from backend based on actual subscription
          nextBilling: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString('es-MX'),
        });
        setLoading(false);
      }, 1000);
    } else {
      setLoading(false);
    }
  }, [sessionId]);

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
            {/* Success Card */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 text-center">
              {/* Success Icon */}
              <div className="mx-auto mb-6 w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>

              {/* Title */}
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                ¡Pago Exitoso!
              </h1>
              <p className="text-lg text-gray-600 mb-8">
                Tu suscripción ya está activa
              </p>

              {loading ? (
                <div className="py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-4 text-gray-600">Cargando detalles de suscripción...</p>
                </div>
              ) : subscriptionInfo ? (
                <>
                  {/* Subscription Details Card */}
                  <div className="bg-gray-50 rounded-lg p-6 mb-8 text-left">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                      Detalles de Suscripción
                    </h2>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Plan:</span>
                        <span className="font-semibold text-gray-900">Plan {subscriptionInfo.plan}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Facturación:</span>
                        <span className="font-semibold text-gray-900">{subscriptionInfo.billing === 'Monthly' ? 'Mensual' : 'Anual'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Monto:</span>
                        <span className="font-semibold text-gray-900">{subscriptionInfo.amount}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Próxima fecha de facturación:</span>
                        <span className="font-semibold text-gray-900">{subscriptionInfo.nextBilling}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Método de pago:</span>
                        <span className="font-semibold text-gray-900">Tarjeta terminada en •••• 4242</span>
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <a
                        href="#"
                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        Descargar recibo →
                      </a>
                    </div>
                  </div>

                  {/* What's Next */}
                  <div className="mb-8 text-left">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                      ¿Qué Sigue?
                    </h2>
                    <ul className="space-y-3">
                      <li className="flex items-start">
                        <span className="text-green-500 mr-3 mt-1">✅</span>
                        <span className="text-gray-700">
                          Las verificaciones ilimitadas ya están activas
                        </span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-3 mt-1">✅</span>
                        <span className="text-gray-700">
                          Acceso completo a datos históricos habilitado
                        </span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-3 mt-1">✅</span>
                        <span className="text-gray-700">
                          Funcionalidad de exportación desbloqueada
                        </span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-3 mt-1">✅</span>
                        <span className="text-gray-700">
                          Credenciales de acceso API enviadas a tu email
                        </span>
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-3 mt-1">✅</span>
                        <span className="text-gray-700">
                          Revisa tu bandeja de entrada para el email de bienvenida
                        </span>
                      </li>
                    </ul>
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-3">
                    <button
                      onClick={() => router.push('/')}
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transition-all"
                    >
                      Ir al Panel
                    </button>
                    <button
                      onClick={() => router.push('/subscription')}
                      className="w-full bg-white border-2 border-gray-300 text-gray-700 py-3 px-6 rounded-lg font-semibold hover:border-gray-400 transition-all"
                    >
                      Ver Configuración de Suscripción
                    </button>
                  </div>
                </>
              ) : (
                <div className="py-8">
                  <p className="text-gray-600 mb-4">
                    No se pudieron cargar los detalles de la suscripción. Por favor revisa la configuración de tu cuenta.
                  </p>
                  <button
                    onClick={() => router.push('/')}
                    className="bg-blue-600 text-white py-2 px-6 rounded-lg font-semibold hover:bg-blue-700"
                  >
                    Ir al Panel
                  </button>
                </div>
              )}

              {/* Footer Info */}
              <div className="mt-8 pt-6 border-t border-gray-200 text-sm text-gray-600">
                <p className="mb-2">
                  ¿Preguntas? Contacta a{' '}
                  <a href="mailto:support@factcheck.mx" className="text-blue-600 hover:underline">
                    support@factcheck.mx
                  </a>
                </p>
                <p className="text-xs text-gray-500">
                  Tu suscripción está gestionada de forma segura por Stripe. Puedes cancelar en cualquier momento desde la configuración de tu cuenta.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default function SubscriptionSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    }>
      <SubscriptionSuccessContent />
    </Suspense>
  );
}


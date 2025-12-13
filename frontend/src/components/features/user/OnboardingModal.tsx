'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBaseUrl } from '@/lib/api-config';

interface OnboardingModalProps {
  onComplete: () => void;
}

const CATEGORIES = [
  { id: 'politics', label: 'Política', icon: '🗳️', description: 'Elecciones, reformas, democracia' },
  { id: 'economy', label: 'Economía', icon: '📈', description: 'Inflación, crecimiento, tipo de cambio' },
  { id: 'security', label: 'Seguridad', icon: '🛡️', description: 'Tasas de homicidio, militarización' },
  { id: 'rights', label: 'Derechos', icon: '⚖️', description: 'Derechos humanos, libertad de expresión' },
  { id: 'environment', label: 'Medio Ambiente', icon: '🌱', description: 'Calidad del aire, agua, clima' },
  { id: 'mexico-us-relations', label: 'México-Estados Unidos', icon: '🌎', description: 'T-MEC, migración, relaciones' },
  { id: 'institutions', label: 'Instituciones', icon: '🏛️', description: 'Poder judicial, reformas institucionales' },
  { id: 'sports', label: 'Deportes', icon: '⚽', description: 'Fútbol, ligas, competencias' },
  { id: 'financial-markets', label: 'Mercados Financieros', icon: '💹', description: 'Bolsa, acciones, inversiones' },
  { id: 'weather', label: 'Clima', icon: '🌦️', description: 'Lluvia, huracanes, temperaturas' },
  { id: 'social-incidents', label: 'Incidentes Sociales', icon: '📢', description: 'Manifestaciones, eventos sociales' },
] as const;

export default function OnboardingModal({ onComplete }: OnboardingModalProps) {
  const router = useRouter();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const handleSubmit = async () => {
    if (selectedCategories.length === 0) {
      setError('Selecciona al menos un tema que te interese');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('No estás autenticado');
      }

      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/auth/me/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          preferred_categories: selectedCategories,
          onboarding_completed: true
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'Error al guardar preferencias');
      }

      onComplete();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar preferencias');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 sm:p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-[#2563EB] to-[#1e40af] mb-4">
              <span className="text-3xl">🇲🇽</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
              Bienvenido a FactCheckr
            </h2>
            <p className="text-gray-600 text-base sm:text-lg">
              La forma más inteligente de entender el futuro de México
            </p>
          </div>

          {/* Instructions */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-900 font-medium mb-1">
              ¿Qué temas de México te importan más?
            </p>
            <p className="text-xs text-blue-700">
              Selecciona los temas que más te interesan. Te mostraremos mercados de predicción relevantes para ti.
            </p>
          </div>

          {/* Category Selection */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            {CATEGORIES.map((category) => {
              const isSelected = selectedCategories.includes(category.id);
              return (
                <button
                  key={category.id}
                  onClick={() => toggleCategory(category.id)}
                  className={`
                    p-4 rounded-xl border-2 transition-all duration-200 text-left
                    ${isSelected
                      ? 'border-[#2563EB] bg-blue-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{category.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className={`font-semibold mb-1 ${isSelected ? 'text-[#2563EB]' : 'text-gray-900'}`}>
                        {category.label}
                      </div>
                      <div className="text-xs text-gray-600">{category.description}</div>
                    </div>
                    {isSelected && (
                      <svg className="w-5 h-5 text-[#2563EB] flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleSubmit}
              disabled={loading || selectedCategories.length === 0}
              className="flex-1 px-6 py-3 bg-[#2563EB] text-white font-semibold rounded-lg hover:bg-[#1d4ed8] disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md hover:shadow-lg"
            >
              {loading ? 'Guardando...' : `Continuar (${selectedCategories.length} seleccionados)`}
            </button>
            <button
              onClick={onComplete}
              className="px-6 py-3 bg-gray-100 text-gray-700 font-semibold rounded-lg hover:bg-gray-200 transition-colors"
            >
              Saltar por ahora
            </button>
          </div>

          {/* Footer Note */}
          <p className="mt-4 text-xs text-gray-500 text-center">
            Puedes cambiar tus preferencias en cualquier momento desde tu perfil
          </p>
        </div>
      </div>
    </div>
  );
}


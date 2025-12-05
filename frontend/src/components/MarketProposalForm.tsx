'use client';

import { useState } from 'react';

interface MarketProposalFormProps {
  onSubmit: (data: {
    question: string;
    description?: string;
    category?: string;
    resolution_criteria?: string;
  }) => Promise<void>;
  onCancel?: () => void;
}

const CATEGORIES = [
  { value: 'politics', label: 'Política' },
  { value: 'economy', label: 'Economía' },
  { value: 'security', label: 'Seguridad' },
  { value: 'rights', label: 'Derechos' },
  { value: 'environment', label: 'Medio Ambiente' },
  { value: 'mexico-us-relations', label: 'México-Estados Unidos' },
  { value: 'institutions', label: 'Instituciones' },
];

export default function MarketProposalForm({ onSubmit, onCancel }: MarketProposalFormProps) {
  const [question, setQuestion] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [resolutionCriteria, setResolutionCriteria] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!question.trim()) {
      setError('La pregunta es requerida');
      return;
    }

    try {
      setSubmitting(true);
      await onSubmit({
        question: question.trim(),
        description: description.trim() || undefined,
        category: category || undefined,
        resolution_criteria: resolutionCriteria.trim() || undefined,
      });
      // Reset form on success
      setQuestion('');
      setDescription('');
      setCategory('');
      setResolutionCriteria('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al enviar propuesta');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div>
        <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
          Pregunta del Mercado *
        </label>
        <input
          type="text"
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ej: ¿El PIB de México crecerá más del 3% en 2024?"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          Formula una pregunta clara que pueda responderse con SÍ o NO
        </p>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          Descripción (opcional)
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Proporciona contexto adicional sobre el mercado..."
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
          Categoría (opcional)
        </label>
        <select
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Seleccionar categoría</option>
          {CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="resolution_criteria" className="block text-sm font-medium text-gray-700 mb-2">
          Criterios de Resolución (opcional)
        </label>
        <textarea
          id="resolution_criteria"
          value={resolutionCriteria}
          onChange={(e) => setResolutionCriteria(e.target.value)}
          placeholder="Especifica cómo se determinará el resultado (fuente de datos, fecha límite, etc.)"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="mt-1 text-xs text-gray-500">
          Ej: "Resuelto según datos oficiales de INEGI publicados antes del 31 de diciembre de 2024"
        </p>
      </div>

      <div className="flex gap-4">
        <button
          type="submit"
          disabled={submitting}
          className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {submitting ? 'Enviando...' : 'Enviar Propuesta'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium"
          >
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}


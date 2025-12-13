'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';
import MarketProposalForm from '@/components/features/markets/MarketProposalForm';
import { getApiBaseUrl } from '@/lib/api-config';

interface Proposal {
  id: number;
  question: string;
  description?: string;
  category?: string;
  resolution_criteria?: string;
  status: string;
  created_at: string;
}

export default function ProposeMarketPage() {
  const router = useRouter();
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchProposals = async () => {
      try {
        const baseUrl = getApiBaseUrl();
        const token = localStorage.getItem('token');
        
        if (!token) {
          router.push('/');
          return;
        }

        // Note: This endpoint would need to be created to list user's proposals
        // For now, we'll just show the form
        setLoading(false);
      } catch (err) {
        console.error('Error fetching proposals:', err);
        setLoading(false);
      }
    };

    fetchProposals();
  }, [router]);

  const handleSubmit = async (data: {
    question: string;
    description?: string;
    category?: string;
    resolution_criteria?: string;
  }) => {
    const baseUrl = getApiBaseUrl();
    const token = localStorage.getItem('token');

    if (!token) {
      router.push('/');
      return;
    }

    const response = await fetch(`${baseUrl}/api/markets/propose`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (response.status === 403) {
      throw new Error('Esta función requiere una suscripción Pro');
    }

    if (response.status === 429) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Límite de propuestas alcanzado. Actualiza a Pro para más propuestas.');
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al enviar propuesta');
    }

    const proposal = await response.json();
    setProposals([...proposals, proposal]);
    
    // Show success message
    alert('Propuesta enviada exitosamente. Será revisada por un administrador.');
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      pending: { label: 'Pendiente', className: 'bg-yellow-100 text-yellow-800' },
      approved: { label: 'Aprobada', className: 'bg-green-100 text-green-800' },
      rejected: { label: 'Rechazada', className: 'bg-red-100 text-red-800' },
    };

    const statusInfo = statusMap[status] || { label: status, className: 'bg-gray-100 text-gray-800' };
    
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${statusInfo.className}`}>
        {statusInfo.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="ml-64 p-8">
        <Header 
          searchQuery={searchQuery} 
          setSearchQuery={setSearchQuery}
          onSearch={() => {}}
        />
        
        <div className="mt-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Proponer Nuevo Mercado</h1>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Proposal Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Nueva Propuesta</h2>
              <MarketProposalForm onSubmit={handleSubmit} />
            </div>

            {/* Existing Proposals */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Mis Propuestas</h2>
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                </div>
              ) : proposals.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No has enviado propuestas aún.</p>
                  <p className="text-sm mt-2">Completa el formulario para crear tu primera propuesta.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {proposals.map((proposal) => (
                    <div key={proposal.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-medium text-gray-900">{proposal.question}</h3>
                        {getStatusBadge(proposal.status)}
                      </div>
                      {proposal.description && (
                        <p className="text-sm text-gray-600 mb-2">{proposal.description}</p>
                      )}
                      {proposal.category && (
                        <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {proposal.category}
                        </span>
                      )}
                      <p className="text-xs text-gray-500 mt-2">
                        Enviado: {new Date(proposal.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">¿Cómo funciona?</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Envía una propuesta de mercado con una pregunta clara</li>
              <li>Un administrador revisará y aprobará tu propuesta</li>
              <li>Una vez aprobada, el mercado estará disponible para operar</li>
              <li>Usuarios Free: 2 propuestas/mes | Pro: 10 propuestas/mes</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}


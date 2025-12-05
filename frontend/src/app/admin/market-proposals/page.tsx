'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import { getApiBaseUrl } from '@/lib/api-config';

interface Proposal {
  id: number;
  user_id: number;
  question: string;
  description?: string;
  category?: string;
  resolution_criteria?: string;
  status: string;
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: number;
}

export default function AdminMarketProposalsPage() {
  const router = useRouter();
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'pending' | 'all'>('pending');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchProposals();
  }, [filter]);

  const fetchProposals = async () => {
    try {
      setLoading(true);
      const baseUrl = getApiBaseUrl();
      const token = localStorage.getItem('token');
      
      if (!token) {
        router.push('/');
        return;
      }

      const statusParam = filter === 'pending' ? '?status=pending' : '';
      const response = await fetch(`${baseUrl}/api/markets/admin/proposals${statusParam}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 403) {
        alert('No tienes permisos de administrador');
        router.push('/');
        return;
      }

      if (!response.ok) {
        throw new Error('Error al cargar propuestas');
      }

      const data = await response.json();
      setProposals(data);
    } catch (err) {
      console.error('Error fetching proposals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (proposalId: number) => {
    if (!confirm('¿Aprobar esta propuesta y crear el mercado?')) {
      return;
    }

    try {
      const baseUrl = getApiBaseUrl();
      const token = localStorage.getItem('token');

      const response = await fetch(`${baseUrl}/api/markets/admin/proposals/${proposalId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al aprobar propuesta');
      }

      const market = await response.json();
      alert(`Mercado creado exitosamente: ${market.question}`);
      fetchProposals();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al aprobar propuesta');
    }
  };

  const handleReject = async (proposalId: number) => {
    if (!confirm('¿Rechazar esta propuesta?')) {
      return;
    }

    try {
      const baseUrl = getApiBaseUrl();
      const token = localStorage.getItem('token');

      const response = await fetch(`${baseUrl}/api/markets/admin/proposals/${proposalId}/reject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al rechazar propuesta');
      }

      alert('Propuesta rechazada');
      fetchProposals();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al rechazar propuesta');
    }
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
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Revisar Propuestas de Mercados</h1>
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('pending')}
                className={`px-4 py-2 rounded ${
                  filter === 'pending'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Pendientes
              </button>
              <button
                onClick={() => setFilter('all')}
                className={`px-4 py-2 rounded ${
                  filter === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Todas
              </button>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Cargando propuestas...</p>
            </div>
          ) : proposals.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-600">No hay propuestas {filter === 'pending' ? 'pendientes' : ''}.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {proposals.map((proposal) => (
                <div key={proposal.id} className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{proposal.question}</h3>
                        {getStatusBadge(proposal.status)}
                      </div>
                      {proposal.description && (
                        <p className="text-gray-600 mb-3">{proposal.description}</p>
                      )}
                      {proposal.category && (
                        <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded mb-2">
                          {proposal.category}
                        </span>
                      )}
                      {proposal.resolution_criteria && (
                        <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded">
                          <p className="text-sm font-medium text-amber-900 mb-1">Criterios de Resolución:</p>
                          <p className="text-sm text-amber-800">{proposal.resolution_criteria}</p>
                        </div>
                      )}
                      <p className="text-xs text-gray-500 mt-3">
                        Enviado: {new Date(proposal.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  
                  {proposal.status === 'pending' && (
                    <div className="flex gap-3 mt-4">
                      <button
                        onClick={() => handleApprove(proposal.id)}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-medium"
                      >
                        Aprobar y Crear Mercado
                      </button>
                      <button
                        onClick={() => handleReject(proposal.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-medium"
                      >
                        Rechazar
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


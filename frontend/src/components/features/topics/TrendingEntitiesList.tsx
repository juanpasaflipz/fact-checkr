'use client';

import { useEffect, useState } from 'react';

interface TrendingEntity {
  id: number;
  name: string;
  type: string;
  claim_count: number;
}

interface TrendingEntitiesListProps {
  days: number;
}

const entityTypeIcons: Record<string, string> = {
  person: '👤',
  institution: '🏛️',
  location: '📍',
  unknown: '🔍'
};

const entityTypeLabels: Record<string, string> = {
  person: 'Persona',
  institution: 'Institución',
  location: 'Ubicación',
  unknown: 'Otro'
};

export default function TrendingEntitiesList({ days }: TrendingEntitiesListProps) {
  const [entities, setEntities] = useState<TrendingEntity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEntities = async () => {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/trends/entities?days=${days}&limit=15`);
        
        if (response.ok) {
          const data = await response.json();
          setEntities(data);
        }
      } catch (error) {
        console.error('Error fetching trending entities:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEntities();
  }, [days]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Entidades Mencionadas</h3>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">Entidades Mencionadas</h3>
        <span className="text-sm text-gray-500">{entities.length} entidades</span>
      </div>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {entities.map((entity, index) => (
          <div
            key={entity.id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="flex-shrink-0">
                <span className="text-2xl">{entityTypeIcons[entity.type] || entityTypeIcons.unknown}</span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-gray-900 truncate group-hover:text-[#2563EB] transition-colors">
                  {entity.name}
                </p>
                <p className="text-xs text-gray-500">
                  {entityTypeLabels[entity.type] || entityTypeLabels.unknown}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-lg font-bold text-gray-900">{entity.claim_count}</span>
              <span className="text-xs text-gray-500">menciones</span>
            </div>
          </div>
        ))}
      </div>

      {entities.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No hay entidades en tendencia en este período</p>
        </div>
      )}
    </div>
  );
}


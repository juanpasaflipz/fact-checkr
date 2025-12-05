'use client';

interface LeaderboardEntry {
  rank: number;
  username: string;
  accuracy_rate: number;
  total_trades: number;
  total_volume: number;
  credits_earned: number;
}

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  metric: 'accuracy' | 'volume' | 'trades';
}

export default function Leaderboard({ entries, metric }: LeaderboardProps) {
  const getMetricLabel = () => {
    switch (metric) {
      case 'accuracy':
        return 'Precisión';
      case 'volume':
        return 'Volumen';
      case 'trades':
        return 'Operaciones';
      default:
        return '';
    }
  };

  const getMetricValue = (entry: LeaderboardEntry) => {
    switch (metric) {
      case 'accuracy':
        return `${(entry.accuracy_rate * 100).toFixed(1)}%`;
      case 'volume':
        return `${entry.total_volume.toFixed(2)} créditos`;
      case 'trades':
        return entry.total_trades.toString();
      default:
        return '';
    }
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) {
      return '🥇';
    } else if (rank === 2) {
      return '🥈';
    } else if (rank === 3) {
      return '🥉';
    }
    return `#${rank}`;
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">
          Clasificación por {getMetricLabel()}
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Posición
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Usuario
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {getMetricLabel()}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Operaciones
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Créditos Ganados
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {entries.map((entry) => (
              <tr key={entry.rank} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-lg font-semibold text-gray-900">
                    {getRankBadge(entry.rank)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{entry.username}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-semibold text-blue-600">
                    {getMetricValue(entry)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {entry.total_trades}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {entry.credits_earned.toFixed(2)} créditos
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {entries.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>No hay datos disponibles aún.</p>
        </div>
      )}
    </div>
  );
}


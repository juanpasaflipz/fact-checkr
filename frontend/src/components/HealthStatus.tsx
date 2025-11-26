'use client';

import { useEffect, useState } from 'react';

type Status = 'healthy' | 'unhealthy' | 'checking';

interface HealthData {
  status: string;
  database: string;
  message?: string;
}

export default function HealthStatus() {
  const [status, setStatus] = useState<Status>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkHealth = async () => {
    setStatus('checking');
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${baseUrl}/health`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' }
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data: HealthData = await response.json();
        setStatus(data.status === 'healthy' ? 'healthy' : 'unhealthy');
      } else {
        setStatus('unhealthy');
      }
    } catch {
      setStatus('unhealthy');
    }
    setLastChecked(new Date());
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const statusConfig = {
    healthy: {
      color: 'bg-green-500',
      pulseColor: 'bg-green-400',
      label: 'En línea',
      textColor: 'text-green-700'
    },
    unhealthy: {
      color: 'bg-red-500',
      pulseColor: 'bg-red-400',
      label: 'Sin conexión',
      textColor: 'text-red-700'
    },
    checking: {
      color: 'bg-yellow-500',
      pulseColor: 'bg-yellow-400',
      label: 'Verificando...',
      textColor: 'text-yellow-700'
    }
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2 text-sm">
      <div className="relative flex items-center justify-center">
        <span className={`absolute inline-flex h-3 w-3 animate-ping rounded-full ${config.pulseColor} opacity-75`}></span>
        <span className={`relative inline-flex h-3 w-3 rounded-full ${config.color}`}></span>
      </div>
      <span className={`font-medium ${config.textColor}`}>{config.label}</span>
      {lastChecked && (
        <span className="text-gray-400 text-xs">
          · {lastChecked.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })}
        </span>
      )}
    </div>
  );
}


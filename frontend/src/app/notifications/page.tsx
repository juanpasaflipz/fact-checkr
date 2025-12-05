'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import { getApiBaseUrl } from '@/lib/api-config';

interface Notification {
  id: number;
  market_id: number;
  notification_type: string;
  message?: string;
  read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const baseUrl = getApiBaseUrl();
      const token = localStorage.getItem('token');
      
      if (!token) {
        router.push('/');
        return;
      }

      const unreadParam = filter === 'unread' ? '?unread_only=true' : '';
      const response = await fetch(`${baseUrl}/api/markets/notifications${unreadParam}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 403) {
        alert('Esta función requiere una suscripción Pro');
        router.push('/subscription');
        return;
      }

      if (!response.ok) {
        throw new Error('Error al cargar notificaciones');
      }

      const data = await response.json();
      setNotifications(data);
    } catch (err) {
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: number) => {
    try {
      const baseUrl = getApiBaseUrl();
      const token = localStorage.getItem('token');

      await fetch(`${baseUrl}/api/markets/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      fetchNotifications();
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      const baseUrl = getApiBaseUrl();
      const token = localStorage.getItem('token');

      await fetch(`${baseUrl}/api/markets/notifications/read-all`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      fetchNotifications();
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    router.push(`/markets/${notification.market_id}`);
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'probability_change':
        return '📊';
      case 'resolution':
        return '✅';
      case 'new_market':
        return '🆕';
      default:
        return '🔔';
    }
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
            <h1 className="text-2xl font-bold text-gray-900">Notificaciones</h1>
            <div className="flex gap-2">
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
              <button
                onClick={() => setFilter('unread')}
                className={`px-4 py-2 rounded ${
                  filter === 'unread'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                No leídas
              </button>
              {notifications.some(n => !n.read) && (
                <button
                  onClick={markAllAsRead}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Marcar todas como leídas
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Cargando notificaciones...</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-600">No hay notificaciones {filter === 'unread' ? 'no leídas' : ''}.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow ${
                    !notification.read ? 'border-l-4 border-blue-600' : ''
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className="text-2xl">{getNotificationIcon(notification.notification_type)}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {!notification.read && (
                          <span className="h-2 w-2 bg-blue-600 rounded-full"></span>
                        )}
                        <span className="text-xs text-gray-500">
                          {new Date(notification.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-gray-900">{notification.message}</p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/markets/${notification.market_id}`);
                        }}
                        className="mt-3 text-sm text-blue-600 hover:text-blue-800"
                      >
                        Ver mercado →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


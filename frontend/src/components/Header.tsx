'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getApiBaseUrl } from '@/lib/api-config';
import { useAuth } from '@/contexts/AuthContext';

interface HeaderProps {
  searchQuery?: string;
  setSearchQuery?: (query: string) => void;
  onSearch?: (e: React.FormEvent) => void;
}

interface UserBalance {
  available_credits: number;
  locked_credits: number;
}

export default function Header({ searchQuery = '', setSearchQuery, onSearch }: HeaderProps) {
  const { user, isAuthenticated, logout } = useAuth();
  const [balance, setBalance] = useState<UserBalance | null>(null);
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);
  
  // Use local state if setSearchQuery is not provided (for Server Components)
  const effectiveSearchQuery = setSearchQuery ? searchQuery : localSearchQuery;
  const effectiveSetSearchQuery = setSearchQuery || setLocalSearchQuery;
  const effectiveOnSearch = onSearch || ((e: React.FormEvent) => {
    e.preventDefault();
    // Could navigate to search page if needed
  });

  useEffect(() => {
    const fetchBalance = async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      // Check if token exists and is not empty
      if (!token || token.trim() === '') return;

      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/markets/balance`, {
          headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${token.trim()}`
          }
        });

        if (response.ok) {
          const data: UserBalance = await response.json();
          setBalance(data);
        } else if (response.status === 401 || response.status === 422) {
          // Token is invalid, clear it and don't retry
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
          }
          setBalance(null);
        }
      } catch (error) {
        console.error('Error fetching balance:', error);
      }
    };

    fetchBalance();
    // Refresh balance every 30 seconds
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex-1 max-w-2xl">
          <form onSubmit={effectiveOnSearch} className="relative">
            <svg className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 size-5 z-10"
                 fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="search"
              value={effectiveSearchQuery}
              onChange={(e) => effectiveSetSearchQuery(e.target.value)}
              placeholder="Buscar temas, personas o noticias..."
              className="
                pl-12 pr-4 py-2.5 w-full 
                bg-white 
                border border-gray-300 
                rounded-lg text-sm 
                focus:border-gray-400 
                focus:ring-1 focus:ring-gray-400 focus:ring-opacity-50
                transition-all duration-200 
                text-gray-900 placeholder-gray-500 
                font-normal
                hover:border-gray-400
              "
            />
          </form>
        </div>
        
        <div className="flex items-center gap-4 ml-6">
          <button className="relative p-2.5 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors duration-200"
                  title="Notificaciones">
            <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute top-1.5 right-1.5 size-2.5 bg-red-500 rounded-full border-2 border-white"></span>
          </button>
          
          {balance && (
            <div className="hidden sm:flex items-center gap-2.5 px-4 py-2 bg-gray-50 rounded-lg border border-gray-200 transition-colors duration-200 hover:bg-gray-100">
              <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-semibold text-gray-900">
                {balance.available_credits.toFixed(0)} créditos
              </span>
            </div>
          )}
          
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
              <div className="text-right hidden sm:block">
                <p className="text-sm text-gray-900 font-semibold">
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>
              <div className="size-10 rounded-lg bg-gray-900 flex items-center justify-center text-white font-semibold text-sm">
                {user.full_name 
                  ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
                  : user.username.slice(0, 2).toUpperCase()}
              </div>
              <button
                onClick={logout}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors duration-200"
                title="Cerrar sesión"
              >
                Salir
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
              <Link
                href="/signin"
                className="px-4 py-2 text-sm font-semibold text-gray-900 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors duration-200 border border-gray-300 hover:border-gray-400"
              >
                Iniciar Sesión
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

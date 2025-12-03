'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getApiBaseUrl } from '@/lib/api-config';
import { useAuth } from '@/contexts/AuthContext';

interface HeaderProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onSearch: (e: React.FormEvent) => void;
}

interface UserBalance {
  available_credits: number;
  locked_credits: number;
}

export default function Header({ searchQuery, setSearchQuery, onSearch }: HeaderProps) {
  const { user, isAuthenticated, logout } = useAuth();
  const [balance, setBalance] = useState<UserBalance | null>(null);

  useEffect(() => {
    const fetchBalance = async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      if (!token) return;

      try {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/markets/balance`, {
          headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data: UserBalance = await response.json();
          setBalance(data);
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
    <header className="sticky top-0 z-40 bg-[#0a0a0f]/95 backdrop-blur-lg border-b-2 border-[#00f0ff]/30 shadow-lg"
            style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.2)' }}>
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex-1 max-w-2xl">
          <form onSubmit={onSearch} className="relative group">
            <svg className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#00f0ff]/60 size-5 group-focus-within:text-[#00f0ff] transition-all duration-300 group-focus-within:scale-110 z-10"
                 style={{ filter: 'drop-shadow(0 0 3px rgba(0, 240, 255, 0.5))' }}
                 fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar temas, personas o noticias..."
              className="
                pl-12 pr-4 py-3 w-full 
                bg-[#111118] 
                border-2 border-[#00f0ff]/30 
                rounded-lg text-sm 
                focus-visible:border-[#00f0ff] 
                focus-visible:bg-[#1a1a24]
                transition-all duration-300 
                text-[#00f0ff] placeholder-gray-500 
                font-semibold
                hover:border-[#00f0ff]/50
              "
              style={{
                boxShadow: '0 0 15px rgba(0, 240, 255, 0.1)'
              }}
              onFocus={(e) => {
                e.currentTarget.style.boxShadow = '0 0 25px rgba(0, 240, 255, 0.4)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.boxShadow = '0 0 15px rgba(0, 240, 255, 0.1)';
              }}
            />
          </form>
        </div>
        
        <div className="flex items-center gap-4 ml-6">
          <button className="relative p-2.5 text-[#00f0ff]/60 hover:text-[#00f0ff] hover:bg-[#111118] rounded-lg transition-all duration-300 hover:scale-110 border-2 border-transparent hover:border-[#00f0ff]/50"
                  style={{ boxShadow: '0 0 10px rgba(0, 240, 255, 0.1)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.boxShadow = '0 0 20px rgba(0, 240, 255, 0.4)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.boxShadow = '0 0 10px rgba(0, 240, 255, 0.1)';
                  }}>
            <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                 style={{ filter: 'drop-shadow(0 0 3px currentColor)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute top-1.5 right-1.5 size-2.5 bg-[#ff00ff] rounded-full border-2 border-[#0a0a0f] shadow-lg animate-pulse"
                  style={{ boxShadow: '0 0 10px rgba(255, 0, 255, 0.8)' }}></span>
          </button>
          
          {balance && (
            <div className="hidden sm:flex items-center gap-2.5 px-4 py-2 bg-[#111118] rounded-lg border-2 border-[#00f0ff]/50 transition-all duration-300 hover:scale-105"
                 style={{ boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)' }}
                 onMouseEnter={(e) => {
                   e.currentTarget.style.boxShadow = '0 0 25px rgba(0, 240, 255, 0.5)';
                 }}
                 onMouseLeave={(e) => {
                   e.currentTarget.style.boxShadow = '0 0 15px rgba(0, 240, 255, 0.3)';
                 }}>
              <svg className="w-5 h-5 text-[#00f0ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                   style={{ filter: 'drop-shadow(0 0 3px #00f0ff)' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-bold text-[#00f0ff]"
                    style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.5)' }}>
                {balance.available_credits.toFixed(0)} créditos
              </span>
            </div>
          )}
          
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3 pl-4 border-l-2 border-[#00f0ff]/30">
              <div className="text-right hidden sm:block">
                <p className="text-sm text-[#00f0ff] font-bold"
                   style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.3)' }}>
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-gray-400 font-medium">{user.email}</p>
              </div>
              <div className="size-11 rounded-lg bg-[#111118] p-0.5 border-2 border-[#00f0ff]/50 hover:border-[#00f0ff] transition-all duration-300 hover:scale-110"
                   style={{ boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)' }}>
                <div className="w-full h-full rounded-lg bg-[#1a1a24] flex items-center justify-center text-[#00f0ff] font-bold text-sm"
                     style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.5)' }}>
                  {user.full_name 
                    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
                    : user.username.slice(0, 2).toUpperCase()}
                </div>
              </div>
              <button
                onClick={logout}
                className="px-3 py-2 text-sm text-[#00f0ff]/60 hover:text-[#00f0ff] hover:bg-[#111118] rounded-lg transition-all duration-300 border-2 border-transparent hover:border-[#00f0ff]/50"
                title="Cerrar sesión"
              >
                Salir
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3 pl-4 border-l-2 border-[#00f0ff]/30">
              <Link
                href="/signin"
                className="px-4 py-2 text-sm font-semibold text-[#00f0ff] hover:bg-[#111118] rounded-lg transition-all duration-300 border-2 border-[#00f0ff]/50 hover:border-[#00f0ff]"
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

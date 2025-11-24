'use client';

import React from 'react';

interface HeaderProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onSearch: (e: React.FormEvent) => void;
}

export default function Header({ searchQuery, setSearchQuery, onSearch }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex-1 max-w-2xl">
          <form onSubmit={onSearch} className="relative group">
            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 size-5 group-focus-within:text-[#2563EB] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar temas, personas o noticias..."
              className="pl-10 pr-4 py-2 w-full bg-[#F8F9FA] border-0 rounded-xl text-sm focus-visible:ring-2 focus-visible:ring-[#2563EB] focus-visible:bg-white transition-all text-gray-900 placeholder-gray-400 font-medium"
            />
          </form>
        </div>
        
        <div className="flex items-center gap-4 ml-6">
          <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-[#F8F9FA] rounded-full transition-colors">
            <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute top-1 right-1 size-2 bg-[#F97316] rounded-full border-2 border-white"></span>
          </button>
          
          <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
            <div className="text-right hidden sm:block">
              <p className="text-sm text-gray-900 font-semibold">Juan Pérez</p>
              <p className="text-xs text-gray-500">Analista Senior</p>
            </div>
            <div className="size-10 rounded-full bg-gradient-to-br from-[#2563EB] to-[#1e40af] p-0.5">
              <div className="w-full h-full rounded-full bg-white p-0.5">
                <div className="w-full h-full rounded-full bg-gray-100 flex items-center justify-center text-white font-semibold text-sm">
                  JP
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

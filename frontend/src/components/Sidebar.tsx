'use client';

import { useState } from 'react';

const menuItems = [
  { id: 'inicio', label: 'Inicio', icon: 'Home' },
  { id: 'tendencias', label: 'Tendencias', icon: 'TrendingUp' },
  { id: 'temas', label: 'Temas', icon: 'Hash' },
  { id: 'fuentes', label: 'Fuentes', icon: 'Folder' },
  { id: 'estadisticas', label: 'Estadísticas', icon: 'BarChart3' },
];

export default function Sidebar() {
  const [activeItem, setActiveItem] = useState('inicio');

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200 shadow-lg">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-6 border-b border-gray-100">
            <div className="flex items-center justify-center size-10 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#1e40af] shadow-lg shadow-[#2563EB]/25">
              <div className="size-6 bg-white rounded-md flex items-center justify-center">
                <div className="size-3 bg-[#2563EB] rounded-sm"></div>
              </div>
            </div>
            <span className="text-xl text-gray-900 font-bold">FactCheckr</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {menuItems.map((item) => {
              const isActive = activeItem === item.id;
              
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveItem(item.id)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                    ${isActive 
                      ? 'bg-gradient-to-r from-[#2563EB] to-[#1e40af] text-white shadow-md shadow-[#2563EB]/20' 
                      : 'text-gray-600 hover:bg-[#F8F9FA] hover:text-gray-900'
                    }
                  `}
                >
                  <Icon name={item.icon} className="size-5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Pro Version Banner */}
          <div className="p-4 m-4 rounded-xl bg-gradient-to-br from-[#F97316] to-[#ea580c] text-white shadow-lg">
            <p className="text-xs mb-2 font-semibold">Versión Pro</p>
            <p className="text-xs mb-3 opacity-90">
              Accede a análisis avanzados y reportes detallados
            </p>
            <button className="w-full px-3 py-2 text-xs bg-white text-[#F97316] rounded-lg hover:bg-gray-50 transition-colors shadow-md font-medium">
              Actualizar Plan
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile Bottom Nav */}
      <div className="lg:hidden fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 shadow-lg z-50">
        <nav className="flex justify-around items-center px-2 py-3">
          {menuItems.slice(0, 4).map((item) => {
            const isActive = activeItem === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveItem(item.id)}
                className={`
                  flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all
                  ${isActive 
                    ? 'text-[#2563EB]' 
                    : 'text-gray-500'
                  }
                `}
              >
                <Icon name={item.icon} className="size-5" />
                <span className="text-xs">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </>
  );
}

function Icon({ name, className }: { name: string; className?: string }) {
  switch (name) {
    case "Home":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>;
    case "TrendingUp":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>;
    case "Hash":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" /></svg>;
    case "Folder":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>;
    case "BarChart3":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>;
    default:
      return null;
  }
}

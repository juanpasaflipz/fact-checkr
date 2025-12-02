'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';

const menuItems = [
  { id: 'inicio', label: 'Inicio', icon: 'Home', path: '/' },
  { id: 'tendencias', label: 'Tendencias', icon: 'TrendingUp', path: '/tendencias' },
  { id: 'mercados', label: 'Mercados', icon: 'TrendingDown', path: '/markets' },
  { id: 'temas', label: 'Temas', icon: 'Hash', path: '/temas' },
  { id: 'fuentes', label: 'Fuentes', icon: 'Folder', path: '/fuentes' },
  { id: 'estadisticas', label: 'Estadísticas', icon: 'BarChart3', path: '/estadisticas' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col grow bg-[#0a0a0f] border-r-2 border-[#00f0ff]/30"
             style={{ boxShadow: '0 0 30px rgba(0, 240, 255, 0.1)' }}>
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-6 border-b-2 border-[#00f0ff]/20 bg-[#111118]">
            <div className="flex items-center justify-center size-12 rounded-lg bg-[#1a1a24] border-2 border-[#00f0ff]/50 hover:border-[#00f0ff] transition-all duration-300 hover:scale-110"
                 style={{ boxShadow: '0 0 20px rgba(0, 240, 255, 0.4)' }}>
              <div className="size-7 bg-[#0a0a0f] rounded-md flex items-center justify-center border border-[#00f0ff]/30">
                <div className="size-4 bg-gradient-to-br from-[#00f0ff] to-[#0066ff] rounded-sm"
                     style={{ boxShadow: '0 0 10px rgba(0, 240, 255, 0.6)' }}></div>
              </div>
            </div>
            <span className="text-xl font-bold text-[#00f0ff]"
                  style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>FactCheckr</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {menuItems.map((item) => {
              // Match exact path or paths that start with the item path (for sub-routes)
              const isActive = pathname === item.path || 
                (item.path !== '/' && pathname.startsWith(item.path + '/'));
              
              return (
                <Link
                  key={item.id}
                  href={item.path}
                  className={`
                    group w-full flex items-center gap-3 px-4 py-3.5 rounded-lg 
                    transition-all duration-300 font-bold
                    border-2
                    ${isActive 
                      ? 'bg-[#1a1a24] border-[#00f0ff] text-[#00f0ff] scale-105' 
                      : 'border-transparent text-gray-400 hover:bg-[#111118] hover:border-[#00f0ff]/30 hover:text-[#00f0ff] hover:scale-105'
                    }
                  `}
                  style={isActive ? {
                    boxShadow: '0 0 20px rgba(0, 240, 255, 0.4), inset 0 0 20px rgba(0, 240, 255, 0.1)'
                  } : {}}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.boxShadow = '0 0 15px rgba(0, 240, 255, 0.2)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.boxShadow = '';
                    }
                  }}
                >
                  <Icon name={item.icon} className={`size-5 ${isActive ? 'text-[#00f0ff]' : 'text-gray-500 group-hover:text-[#00f0ff]'} transition-colors`}
                        style={isActive ? { filter: 'drop-shadow(0 0 3px #00f0ff)' } : {}} />
                  <span style={isActive ? { textShadow: '0 0 5px rgba(0, 240, 255, 0.5)' } : {}}>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Pro Version Banner */}
          <div className="p-5 m-4 rounded-lg bg-[#1a1a24] border-2 border-[#ff00ff]/50 hover:border-[#ff00ff] transition-all duration-300 hover:scale-105"
               style={{ boxShadow: '0 0 25px rgba(255, 0, 255, 0.3), inset 0 0 25px rgba(255, 0, 255, 0.05)' }}>
            <p className="text-sm mb-2 font-bold text-[#ff00ff]"
               style={{ textShadow: '0 0 5px rgba(255, 0, 255, 0.5)' }}>Versión Pro</p>
            <p className="text-xs mb-4 text-gray-300 font-medium">
              Accede a análisis avanzados y reportes detallados
            </p>
            <Link href="/subscription">
              <button className="w-full px-4 py-2.5 text-xs bg-gradient-to-r from-[#ff00ff] to-[#ff0066] text-white rounded-lg hover:from-[#ff00ff] hover:to-[#ff00aa] transition-all duration-300 font-bold hover:scale-105 border-2 border-[#ff00ff]"
                      style={{ boxShadow: '0 0 15px rgba(255, 0, 255, 0.5)' }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.boxShadow = '0 0 25px rgba(255, 0, 255, 0.8)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.boxShadow = '0 0 15px rgba(255, 0, 255, 0.5)';
                      }}>
                Actualizar Plan
              </button>
            </Link>
          </div>
        </div>
      </aside>

      {/* Mobile Bottom Nav */}
      <div className="lg:hidden fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 shadow-lg z-50">
        <nav className="flex justify-around items-center px-1 py-2">
          {menuItems.map((item) => {
            // Match exact path or paths that start with the item path (for sub-routes)
            const isActive = pathname === item.path || 
              (item.path !== '/' && pathname.startsWith(item.path + '/'));
            
            return (
              <Link
                key={item.id}
                href={item.path}
                className={`
                  flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition-all flex-1
                  ${isActive 
                    ? 'text-[#2563EB]' 
                    : 'text-gray-500'
                  }
                `}
              >
                <Icon name={item.icon} className="size-5" />
                <span className="text-xs leading-tight">{item.label}</span>
              </Link>
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
    case "TrendingDown":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>;
    default:
      return null;
  }
}

'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';

const menuItems = [
  { id: 'inicio', label: 'Inicio', icon: 'Home', path: '/' },
  { id: 'tendencias', label: 'Tendencias', icon: 'TrendingUp', path: '/tendencias' },
  { id: 'mercados', label: 'Mercados', icon: 'TrendingDown', path: '/markets' },
  { id: 'temas', label: 'Temas', icon: 'Hash', path: '/temas' },
  { id: 'blog', label: 'Blog', icon: 'BookOpen', path: '/blog' },
  { id: 'fuentes', label: 'Fuentes', icon: 'Folder', path: '/fuentes' },
  { id: 'estadisticas', label: 'Estadísticas', icon: 'BarChart3', path: '/estadisticas' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col z-50">
        <div className="flex flex-col grow bg-white border-r border-gray-200 shadow-sm">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-6 border-b border-gray-200 bg-white">
            <div className="flex items-center justify-center size-10 rounded-lg bg-gray-900">
              <div className="size-6 bg-white rounded flex items-center justify-center">
                <div className="size-4 bg-gray-900 rounded-sm"></div>
              </div>
            </div>
            <span className="text-xl font-bold text-gray-900">FactCheckr</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {menuItems.map((item) => {
              // Match exact path or paths that start with the item path (for sub-routes)
              const isActive = pathname === item.path || 
                (item.path !== '/' && pathname.startsWith(item.path + '/'));
              
              return (
                <Link
                  key={item.id}
                  href={item.path}
                  className={`
                    group w-full flex items-center gap-3 px-4 py-3 rounded-lg 
                    transition-all duration-200 font-normal
                    ${isActive 
                      ? 'bg-gray-100 text-gray-900 border-l-4 border-gray-900' 
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon name={item.icon} className={`size-5 ${isActive ? 'text-gray-900' : 'text-gray-500 group-hover:text-gray-700'} transition-colors`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Pro Version Banner */}
          <div className="p-5 m-4 rounded-lg bg-gray-50 border border-gray-200">
            <p className="text-sm mb-2 font-semibold text-gray-900">Versión Pro</p>
            <p className="text-xs mb-4 text-gray-600">
              Accede a análisis avanzados y reportes detallados
            </p>
            <Link href="/subscription">
              <button className="w-full px-4 py-2.5 text-xs bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors duration-200 font-semibold">
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
                  flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition-colors flex-1
                  ${isActive 
                    ? 'text-blue-600' 
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
    case "BookOpen":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>;
    default:
      return null;
  }
}

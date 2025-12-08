'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

interface BlogArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  article_type: string;
  published_at: string | null;
  created_at: string;
}

interface BlogArticleListProps {
  articles: BlogArticle[];
  tier: string;
  freeTierLimit?: number;
}

export default function BlogArticleList({ 
  articles, 
  tier,
  freeTierLimit 
}: BlogArticleListProps) {
  const { isAuthenticated } = useAuth();
  const isFree = tier === 'free';
  
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Fecha no disponible';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };
  
  const getArticleTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'morning': 'Resumen Matutino',
      'afternoon': 'Análisis del Día',
      'evening': 'Resumen Vespertino',
      'breaking': 'Breaking News'
    };
    return labels[type] || type;
  };
  
  return (
    <div>
      {isFree && freeTierLimit && articles.length >= freeTierLimit && (
        <div className="mb-6 p-4 bg-[#1a1a24] border-2 border-[#ff00ff]/50 rounded-lg">
          <p className="text-sm text-gray-300 mb-2">
            Mostrando los {freeTierLimit} artículos más recientes.{' '}
            <Link href="/subscription" className="text-[#ff00ff] hover:underline font-semibold">
              Actualiza a PRO
            </Link>
            {' '}para acceso completo a todos los artículos.
          </p>
        </div>
      )}
      
      {articles.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400 text-lg">No hay artículos disponibles aún.</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <Link
              key={article.id}
              href={`/blog/${article.slug}`}
              className="group block p-6 bg-[#111118] border-2 border-[#00f0ff]/30 rounded-lg hover:border-[#00f0ff] transition-all hover:scale-105 cursor-pointer no-underline"
              style={{ boxShadow: '0 0 15px rgba(0, 240, 255, 0.1)' }}
              prefetch={true}
            >
              <div className="mb-2">
                <span className="text-xs text-[#00f0ff] font-semibold uppercase">
                  {getArticleTypeLabel(article.article_type)}
                </span>
              </div>
              <h2 className="text-xl font-bold text-[#00f0ff] mb-2 line-clamp-2"
                  style={{ textShadow: '0 0 5px rgba(0, 240, 255, 0.3)' }}>
                {article.title}
              </h2>
              {article.excerpt && (
                <p className="text-gray-300 text-sm mb-4 line-clamp-3">
                  {article.excerpt}
                </p>
              )}
              <div className="flex items-center justify-between mt-4">
                <time className="text-xs text-gray-500">
                  {formatDate(article.published_at || article.created_at)}
                </time>
                <span className="text-xs text-[#00f0ff] opacity-0 group-hover:opacity-100 transition-opacity">
                  Leer más →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}


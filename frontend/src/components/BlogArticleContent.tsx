'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from 'next/link';

interface BlogArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  content: string;
  article_type: string;
  published_at: string | null;
  created_at: string;
  telegraph_url: string | null;
  twitter_url: string | null;
  topic_id: number | null;
  data_context?: {
    sources?: {
      url?: string | null;
      platform?: string | null;
      credibility?: number | null;
      engagement?: { likes?: number; retweets?: number; views?: number };
      claim_excerpt?: string;
      status?: string;
    }[];
    evidence?: {
      claim_excerpt?: string;
      status?: string;
      evidence_urls?: string[];
    }[];
    topics?: {
      topic_name?: string;
      claim_count?: number;
      verified_count?: number;
      debunked_count?: number;
    }[];
    deep_topic?: Record<string, unknown> | null;
  };
}

interface BlogArticleContentProps {
  article: BlogArticle;
}

export default function BlogArticleContent({ article }: BlogArticleContentProps) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Fecha no disponible';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
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
    <article className="bg-[#111118] border-2 border-[#00f0ff]/30 rounded-lg p-8">
      {/* Header */}
      <header className="mb-6">
        <div className="mb-4">
          <span className="text-sm text-[#00f0ff] font-semibold uppercase">
            {getArticleTypeLabel(article.article_type)}
          </span>
        </div>
        <h1 className="text-4xl font-bold text-[#00f0ff] mb-4"
            style={{ textShadow: '0 0 10px rgba(0, 240, 255, 0.5)' }}>
          {article.title}
        </h1>
        {article.excerpt && (
          <p className="text-xl text-gray-300 mb-4 italic">
            {article.excerpt}
          </p>
        )}
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <time>{formatDate(article.published_at || article.created_at)}</time>
          {article.telegraph_url && (
            <a
              href={article.telegraph_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#00f0ff] hover:underline"
            >
              Ver en Telegraph
            </a>
          )}
          {article.twitter_url && (
            <a
              href={article.twitter_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#00f0ff] hover:underline"
            >
              Ver en Twitter
            </a>
          )}
        </div>
      </header>
      
      {/* Content */}
      <div className="prose prose-invert max-w-none">
        <div className="text-gray-200 markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({node, ...props}) => <h1 className="text-3xl font-bold text-[#00f0ff] mt-8 mb-4" {...props} />,
              h2: ({node, ...props}) => <h2 className="text-2xl font-bold text-[#00f0ff] mt-6 mb-3" {...props} />,
              h3: ({node, ...props}) => <h3 className="text-xl font-bold text-[#00f0ff] mt-4 mb-2" {...props} />,
              p: ({node, ...props}) => <p className="mb-4 leading-relaxed" {...props} />,
              a: ({node, ...props}) => (
                <a className="text-[#00f0ff] hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
              ),
              ul: ({node, ...props}) => <ul className="list-disc list-inside mb-4 space-y-2" {...props} />,
              ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-4 space-y-2" {...props} />,
              li: ({node, ...props}) => <li className="ml-4" {...props} />,
              strong: ({node, ...props}) => <strong className="font-bold text-[#00f0ff]" {...props} />,
              code: ({node, ...props}) => (
                <code className="bg-[#1a1a24] px-2 py-1 rounded text-sm" {...props} />
              ),
              blockquote: ({node, ...props}) => (
                <blockquote className="border-l-4 border-[#00f0ff] pl-4 italic my-4" {...props} />
              ),
            }}
          >
            {article.content}
          </ReactMarkdown>
        </div>
      </div>
      
      {/* Context & sources */}
      {(article.data_context?.sources?.length || article.data_context?.evidence?.length || article.data_context?.topics?.length) && (
        <section className="mt-8">
          <h3 className="text-2xl font-bold text-[#00f0ff] mb-3">Fuentes y contexto</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {article.data_context?.sources?.length ? (
              <div className="p-4 bg-[#0d0d15] border border-[#00f0ff]/20 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-200 mb-2">Principales fuentes</h4>
                <ul className="space-y-2 text-sm text-gray-300">
                  {article.data_context.sources.slice(0, 5).map((src, idx) => (
                    <li key={idx} className="border-b border-[#00f0ff]/10 pb-2 last:border-none last:pb-0">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 text-xs bg-[#00f0ff]/10 text-[#00f0ff] rounded">
                          {src.platform || 'Fuente'}
                        </span>
                        {typeof src.credibility === 'number' && (
                          <span className="text-xs text-gray-400">Cred: {src.credibility.toFixed(2)}</span>
                        )}
                      </div>
                      {src.url && (
                        <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-[#00f0ff] hover:underline block truncate">
                          {src.url}
                        </a>
                      )}
                      {src.claim_excerpt && <p className="text-gray-400 mt-1 line-clamp-2">{src.claim_excerpt}</p>}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {article.data_context?.evidence?.length ? (
              <div className="p-4 bg-[#0d0d15] border border-[#00f0ff]/20 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-200 mb-2">Evidencia citada</h4>
                <ul className="space-y-3 text-sm text-gray-300">
                  {article.data_context.evidence.slice(0, 4).map((ev, idx) => (
                    <li key={idx} className="border-b border-[#00f0ff]/10 pb-2 last:border-none last:pb-0">
                      {ev.claim_excerpt && <p className="text-gray-400 mb-1 line-clamp-2">{ev.claim_excerpt}</p>}
                      <div className="space-y-1">
                        {ev.evidence_urls?.slice(0, 3).map((url) => (
                          <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="text-[#00f0ff] hover:underline block truncate">
                            {url}
                          </a>
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {article.data_context?.topics?.length ? (
              <div className="p-4 bg-[#0d0d15] border border-[#00f0ff]/20 rounded-lg md:col-span-2">
                <h4 className="text-lg font-semibold text-gray-200 mb-2">Temas destacados</h4>
                <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {article.data_context.topics.map((t, idx) => (
                    <div key={idx} className="p-3 bg-[#111118] border border-[#00f0ff]/10 rounded">
                      <p className="text-[#00f0ff] font-semibold">{t.topic_name}</p>
                      <p className="text-xs text-gray-400 mt-1">Claims: {t.claim_count ?? 0}</p>
                      <p className="text-xs text-gray-400">Verificados: {t.verified_count ?? 0} · Desmentidos: {t.debunked_count ?? 0}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="mt-8 pt-6 border-t-2 border-[#00f0ff]/30">
        <div className="flex items-center justify-between">
          <Link
            href="/blog"
            className="text-[#00f0ff] hover:underline"
          >
            ← Volver al blog
          </Link>
          <div className="flex gap-4">
            {article.telegraph_url && (
              <a
                href={article.telegraph_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-400 hover:text-[#00f0ff]"
              >
                Compartir en Telegraph
              </a>
            )}
            {article.twitter_url && (
              <a
                href={article.twitter_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-400 hover:text-[#00f0ff]"
              >
                Ver en Twitter
              </a>
            )}
          </div>
        </div>
      </footer>
    </article>
  );
}


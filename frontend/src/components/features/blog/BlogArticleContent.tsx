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
    <article className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg p-8 shadow-sm">
      {/* Header */}
      <header className="mb-6">
        <div className="mb-4">
          <span className="text-sm text-[var(--primary-blue)] font-semibold uppercase bg-blue-50 px-2 py-1 rounded-full">
            {getArticleTypeLabel(article.article_type)}
          </span>
        </div>
        <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-4">
          {article.title}
        </h1>
        {article.excerpt && (
          <p className="text-xl text-[var(--text-secondary)] mb-4 italic">
            {article.excerpt}
          </p>
        )}
        <div className="flex items-center gap-4 text-sm text-[var(--text-tertiary)]">
          <time>{formatDate(article.published_at || article.created_at)}</time>
          {article.telegraph_url && (
            <a
              href={article.telegraph_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--primary-blue)] hover:underline"
            >
              Ver en Telegraph
            </a>
          )}
          {article.twitter_url && (
            <a
              href={article.twitter_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--primary-blue)] hover:underline"
            >
              Ver en Twitter
            </a>
          )}
        </div>
      </header>

      {/* Content */}
      <div className="prose prose-lg max-w-none text-[var(--text-primary)]">
        <div className="markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ node, ...props }) => <h1 className="text-3xl font-bold text-[var(--text-primary)] mt-8 mb-4 border-b pb-2" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-2xl font-bold text-[var(--text-primary)] mt-6 mb-3" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-xl font-bold text-[var(--text-primary)] mt-4 mb-2" {...props} />,
              p: ({ node, ...props }) => <p className="mb-4 leading-relaxed text-[var(--text-secondary)]" {...props} />,
              a: ({ node, ...props }) => (
                <a className="text-[var(--primary-blue)] hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
              ),
              ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-4 space-y-2 text-[var(--text-secondary)]" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-4 space-y-2 text-[var(--text-secondary)]" {...props} />,
              li: ({ node, ...props }) => <li className="ml-4" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold text-[var(--text-primary)]" {...props} />,
              code: ({ node, ...props }) => (
                <code className="bg-[var(--bg-tertiary)] text-[var(--text-primary)] px-2 py-1 rounded text-sm" {...props} />
              ),
              blockquote: ({ node, ...props }) => (
                <blockquote className="border-l-4 border-[var(--primary-blue)] pl-4 italic my-4 text-[var(--text-secondary)] bg-[var(--bg-tertiary)] p-4 rounded-r" {...props} />
              ),
            }}
          >
            {article.content}
          </ReactMarkdown>
        </div>
      </div>

      {/* Context & sources */}
      {(article.data_context?.sources?.length || article.data_context?.evidence?.length || article.data_context?.topics?.length) && (
        <section className="mt-8 pt-8 border-t border-[var(--border-color)]">
          <h3 className="text-2xl font-bold text-[var(--text-primary)] mb-4">Fuentes y contexto</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {article.data_context?.sources?.length ? (
              <div className="p-4 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg">
                <h4 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Principales fuentes</h4>
                <ul className="space-y-2 text-sm text-[var(--text-secondary)]">
                  {article.data_context.sources.slice(0, 5).map((src, idx) => (
                    <li key={idx} className="border-b border-[var(--border-color)] pb-2 last:border-none last:pb-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 text-xs bg-blue-50 text-[var(--primary-blue)] rounded font-medium">
                          {src.platform || 'Fuente'}
                        </span>
                        {typeof src.credibility === 'number' && (
                          <span className="text-xs text-[var(--text-tertiary)]">Cred: {src.credibility.toFixed(2)}</span>
                        )}
                      </div>
                      {src.url && (
                        <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-[var(--primary-blue)] hover:underline block truncate mb-1">
                          {src.url}
                        </a>
                      )}
                      {src.claim_excerpt && <p className="text-[var(--text-tertiary)] italic line-clamp-2">"{src.claim_excerpt}"</p>}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {article.data_context?.evidence?.length ? (
              <div className="p-4 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg">
                <h4 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Evidencia citada</h4>
                <ul className="space-y-3 text-sm text-[var(--text-secondary)]">
                  {article.data_context.evidence.slice(0, 4).map((ev, idx) => (
                    <li key={idx} className="border-b border-[var(--border-color)] pb-2 last:border-none last:pb-0">
                      {ev.claim_excerpt && <p className="text-[var(--text-primary)] mb-1 line-clamp-2 font-medium">{ev.claim_excerpt}</p>}
                      <div className="space-y-1 ml-2">
                        {ev.evidence_urls?.slice(0, 3).map((url) => (
                          <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="text-[var(--primary-blue)] hover:underline block truncate text-xs">
                            🔗 {url}
                          </a>
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {article.data_context?.topics?.length ? (
              <div className="p-4 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg md:col-span-2">
                <h4 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Temas destacados</h4>
                <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {article.data_context.topics.map((t, idx) => (
                    <div key={idx} className="p-3 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded shadow-sm">
                      <p className="text-[var(--primary-blue)] font-semibold">{t.topic_name}</p>
                      <div className="flex justify-between mt-2 text-xs text-[var(--text-secondary)]">
                        <span>Claims: {t.claim_count ?? 0}</span>
                        <span className="text-green-600">✓ {t.verified_count ?? 0}</span>
                        <span className="text-red-500">✗ {t.debunked_count ?? 0}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="mt-8 pt-6 border-t border-[var(--border-color)]">
        <div className="flex items-center justify-between">
          <Link
            href="/blog"
            className="text-[var(--primary-blue)] hover:underline font-medium"
          >
            ← Volver al blog
          </Link>
          <div className="flex gap-4">
            {article.telegraph_url && (
              <a
                href={article.telegraph_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-[var(--text-secondary)] hover:text-[var(--primary-blue)]"
              >
                Compartir en Telegraph
              </a>
            )}
            {article.twitter_url && (
              <a
                href={article.twitter_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-[var(--text-secondary)] hover:text-[var(--primary-blue)]"
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


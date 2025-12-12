import { Metadata } from 'next';
import { getApiBaseUrl } from '@/lib/api-config';
import BlogArticleList from '@/components/BlogArticleList';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export const metadata: Metadata = {
  title: 'Blog - FactCheckr MX | Análisis y Verificación de Noticias',
  description: 'Artículos diarios sobre verificación de hechos, análisis de tendencias y desinformación en política mexicana. Resúmenes matutinos, análisis del día y resúmenes vespertinos.',
  keywords: ['fact-checking', 'verificación', 'noticias México', 'política mexicana', 'desinformación', 'análisis'],
  openGraph: {
    title: 'Blog - FactCheckr MX',
    description: 'Análisis diario de verificación de hechos en política mexicana',
    url: 'https://factcheck.mx/blog',
    siteName: 'FactCheckr MX',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Blog - FactCheckr MX',
    description: 'Análisis diario de verificación de hechos',
  },
  alternates: {
    canonical: 'https://factcheck.mx/blog',
  },
};

interface BlogArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  article_type: string;
  published_at: string | null;
  created_at: string;
}

interface BlogResponse {
  articles: BlogArticle[];
  tier: string;
  has_more: boolean;
  free_tier_limit?: number;
}

async function getBlogArticles(): Promise<BlogResponse> {
  const apiUrl = getApiBaseUrl();

  try {
    const url = `${apiUrl}/api/blog/articles?limit=20`;
    console.log('Fetching blog articles from:', url);

    const response = await fetch(url, {
      next: { revalidate: 300 }, // Revalidate every 5 minutes
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Failed to fetch articles:', response.status, errorText);
      throw new Error(`Failed to fetch articles: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching blog articles:', error);
    // Return empty result on error
    return {
      articles: [],
      tier: 'free',
      has_more: false,
    };
  }
}

export default async function BlogPage() {
  const data = await getBlogArticles();

  return (
    <div className="min-h-screen bg-[var(--bg-secondary)] flex">
      <Sidebar />
      <div className="flex-1 lg:ml-64">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-[var(--primary-blue)] mb-4">
              Blog de Verificación
            </h1>
            <p className="text-[var(--text-secondary)] text-lg">
              Análisis diario de verificación de hechos, tendencias y desinformación en política mexicana
            </p>
          </div>

          <BlogArticleList articles={data.articles} tier={data.tier} freeTierLimit={data.free_tier_limit} />
        </main>
      </div>
    </div>
  );
}


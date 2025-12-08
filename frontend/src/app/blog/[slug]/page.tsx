import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getApiBaseUrl } from '@/lib/api-config';
import BlogArticleContent from '@/components/BlogArticleContent';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

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
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const apiUrl = getApiBaseUrl();
  
  try {
    const response = await fetch(`${apiUrl}/api/blog/articles/${params.slug}`, {
      next: { revalidate: 300 },
    });
    
    if (!response.ok) {
      return {
        title: 'Artículo no encontrado - FactCheckr MX',
      };
    }
    
    const article: BlogArticle = await response.json();
    
    return {
      title: `${article.title} - FactCheckr MX`,
      description: article.excerpt || 'Artículo de verificación de hechos',
      openGraph: {
        title: article.title,
        description: article.excerpt || 'Artículo de verificación de hechos',
        url: `https://factcheck.mx/blog/${article.slug}`,
        type: 'article',
        publishedTime: article.published_at || undefined,
      },
      twitter: {
        card: 'summary_large_image',
        title: article.title,
        description: article.excerpt || 'Artículo de verificación de hechos',
      },
      alternates: {
        canonical: `https://factcheck.mx/blog/${article.slug}`,
      },
    };
  } catch {
    return {
      title: 'Artículo - FactCheckr MX',
    };
  }
}

async function getArticle(slug: string): Promise<BlogArticle | { restricted: true } | null> {
  const apiUrl = getApiBaseUrl();
  
  try {
    const response = await fetch(`${apiUrl}/api/blog/articles/${slug}`, {
      next: { revalidate: 300 },
    });
    
    if (!response.ok) {
      if (response.status === 403) {
        // Free tier limitation - return restricted marker
        return { restricted: true };
      }
      return null;
    }
    
    return await response.json();
  } catch {
    return null;
  }
}

export default async function BlogArticlePage({ params }: { params: { slug: string } }) {
  const article = await getArticle(params.slug);
  
  if (!article) {
    notFound();
  }
  
  // Handle free tier restriction
  if ('restricted' in article) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex">
        <Sidebar />
        <div className="flex-1 lg:ml-64">
          <Header />
          <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="bg-[#1a1a24] border-2 border-[#ff00ff]/50 rounded-lg p-8 text-center">
              <h1 className="text-2xl font-bold text-[#ff00ff] mb-4">
                Acceso Limitado
              </h1>
              <p className="text-gray-300 mb-6">
                Este artículo está disponible solo para usuarios PRO. 
                Actualiza tu plan para acceder a todos los artículos del blog.
              </p>
              <a
                href="/subscription"
                className="inline-block px-6 py-3 bg-gradient-to-r from-[#ff00ff] to-[#ff0066] text-white rounded-lg hover:from-[#ff00ff] hover:to-[#ff00aa] transition-all font-bold"
              >
                Actualizar a PRO
              </a>
            </div>
          </main>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-[#0a0a0f] flex">
      <Sidebar />
      <div className="flex-1 lg:ml-64">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <BlogArticleContent article={article} />
        </main>
      </div>
    </div>
  );
}


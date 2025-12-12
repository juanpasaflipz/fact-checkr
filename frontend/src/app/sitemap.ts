import { MetadataRoute } from 'next';
import { getApiBaseUrl } from '@/lib/api-config';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const apiUrl = getApiBaseUrl();

  const baseUrls: MetadataRoute.Sitemap = [
    {
      url: 'https://app.factcheck.mx',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: 'https://app.factcheck.mx/blog',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 0.9,
    },
  ];

  // Fetch blog articles
  try {
    const response = await fetch(`${apiUrl}/api/blog/articles?limit=100`, {
      next: { revalidate: 3600 }, // Revalidate hourly
    });

    if (response.ok) {
      const data = await response.json();
      const blogUrls: MetadataRoute.Sitemap = data.articles.map((article: any) => ({
        url: `https://app.factcheck.mx/blog/${article.slug}`,
        lastModified: article.published_at ? new Date(article.published_at) : new Date(article.created_at),
        changeFrequency: 'daily' as const,
        priority: 0.8,
      }));

      return [...baseUrls, ...blogUrls];
    }
  } catch (error) {
    console.error('Error fetching blog articles for sitemap:', error);
  }

  return baseUrls;
}


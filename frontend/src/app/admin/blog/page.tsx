'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import { getApiBaseUrl } from '@/lib/api-config';
import Link from 'next/link';

interface Article {
    id: number;
    title: string;
    slug: string;
    excerpt?: string;
    article_type: string;
    published_at?: string;
    created_at: string;
    telegraph_url?: string;
    twitter_url?: string;
}

export default function AdminBlogPage() {
    const router = useRouter();
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'published' | 'draft'>('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchArticles();
    }, [filter]);

    const fetchArticles = async () => {
        try {
            setLoading(true);
            const baseUrl = getApiBaseUrl();
            const token = localStorage.getItem('token');

            if (!token) {
                router.push('/');
                return;
            }

            // Using the status param we simplified in the backend
            const statusParam = `?status=${filter}&limit=50`;
            const response = await fetch(`${baseUrl}/api/blog/articles${statusParam}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.status === 403) {
                alert('No tienes permisos de administrador');
                router.push('/');
                return;
            }

            if (!response.ok) {
                throw new Error('Error al cargar artículos');
            }

            const data = await response.json();
            setArticles(data.articles || []);
        } catch (err) {
            console.error('Error fetching articles:', err);
        } finally {
            setLoading(false);
        }
    };

    const handlePublish = async (articleId: number) => {
        if (!confirm('¿Seguro que deseas publicar este artículo? Se enviará a Telegraph.')) {
            return;
        }

        try {
            const baseUrl = getApiBaseUrl();
            const token = localStorage.getItem('token');

            const response = await fetch(`${baseUrl}/api/blog/articles/${articleId}/publish?publish_to_telegraph=true&publish_to_twitter=true`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al publicar artículo');
            }

            alert('Artículo publicado exitosamente');
            fetchArticles(); // Refresh list
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Error al publicar artículo');
        }
    };

    const getStatusBadge = (article: Article) => {
        if (article.published_at) {
            return <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">Publicado</span>;
        }
        return <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">Borrador</span>;
    };

    const getTypeBadge = (type: string) => {
        const types: Record<string, string> = {
            morning: 'bg-orange-100 text-orange-800',
            afternoon: 'bg-blue-100 text-blue-800',
            evening: 'bg-indigo-100 text-indigo-800',
            breaking: 'bg-red-100 text-red-800',
        };
        return (
            <span className={`px-2 py-1 rounded text-xs font-medium ${types[type] || 'bg-gray-100 text-gray-800'}`}>
                {type}
            </span>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Sidebar />
            <div className="ml-64 p-8">
                <Header
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    onSearch={() => { }}
                />

                <div className="mt-8">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <Link href="/admin" className="text-gray-500 hover:text-gray-700">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                </Link>
                                <h1 className="text-2xl font-bold text-gray-900">Gestión de Blog</h1>
                            </div>
                            <p className="text-gray-600 text-sm ml-7">Administra y publica los artículos generados por IA</p>
                        </div>

                        <div className="flex gap-2">
                            <button
                                onClick={() => setFilter('all')}
                                className={`px-3 py-1.5 rounded text-sm ${filter === 'all' ? 'bg-gray-800 text-white' : 'bg-white border text-gray-700'}`}
                            >
                                Todos
                            </button>
                            <button
                                onClick={() => setFilter('draft')}
                                className={`px-3 py-1.5 rounded text-sm ${filter === 'draft' ? 'bg-yellow-600 text-white' : 'bg-white border text-gray-700'}`}
                            >
                                Borradores
                            </button>
                            <button
                                onClick={() => setFilter('published')}
                                className={`px-3 py-1.5 rounded text-sm ${filter === 'published' ? 'bg-green-600 text-white' : 'bg-white border text-gray-700'}`}
                            >
                                Publicados
                            </button>
                        </div>
                    </div>

                    {loading ? (
                        <div className="text-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                            <p className="mt-4 text-gray-600">Cargando artículos...</p>
                        </div>
                    ) : articles.length === 0 ? (
                        <div className="bg-white rounded-lg shadow p-8 text-center">
                            <p className="text-gray-600">No hay artículos encontrados.</p>
                        </div>
                    ) : (
                        <div className="bg-white shadow rounded-lg overflow-hidden">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Artículo</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Creación</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {articles.map((article) => (
                                        <tr key={article.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4">
                                                <div className="text-sm font-medium text-gray-900">{article.title}</div>
                                                <div className="text-xs text-gray-500 truncate max-w-md">{article.slug}</div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {getTypeBadge(article.article_type)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {new Date(article.created_at).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {getStatusBadge(article)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <div className="flex justify-end gap-3">
                                                    <Link
                                                        href={`/blog/${article.slug}`}
                                                        target="_blank"
                                                        className="text-blue-600 hover:text-blue-900"
                                                    >
                                                        Ver
                                                    </Link>
                                                    {!article.published_at && (
                                                        <button
                                                            onClick={() => handlePublish(article.id)}
                                                            className="text-green-600 hover:text-green-900"
                                                        >
                                                            Publicar
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

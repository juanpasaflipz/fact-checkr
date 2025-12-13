'use client';

import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';
import { useState } from 'react';
import Link from 'next/link';

export default function AdminDashboardPage() {
    const [searchQuery, setSearchQuery] = useState('');

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
                    <h1 className="text-3xl font-bold text-gray-900 mb-6">Panel de Administración</h1>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                        {/* Market Proposals Card */}
                        <Link href="/admin/market-proposals" className="block">
                            <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-6 border border-gray-100">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                    </div>
                                    <h2 className="text-xl font-semibold text-gray-900">Propuestas de Mercado</h2>
                                </div>
                                <p className="text-gray-600 mb-4">
                                    Revisar, aprobar o rechazar propuestas de mercados enviadas por los usuarios.
                                </p>
                                <div className="flex items-center text-blue-600 font-medium text-sm">
                                    Gestionar Propuestas
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>
                        </Link>

                        {/* Blog Management Card */}
                        <Link href="/admin/blog" className="block">
                            <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-6 border border-gray-100">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="p-3 bg-purple-100 text-purple-600 rounded-lg">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                                        </svg>
                                    </div>
                                    <h2 className="text-xl font-semibold text-gray-900">Gestión de Blog</h2>
                                </div>
                                <p className="text-gray-600 mb-4">
                                    Ver artículos generados, publicar borradores y gestionar contenido del blog.
                                </p>
                                <div className="flex items-center text-purple-600 font-medium text-sm">
                                    Gestionar Artículos
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>
                        </Link>

                    </div>
                </div>
            </div>
        </div>
    );
}

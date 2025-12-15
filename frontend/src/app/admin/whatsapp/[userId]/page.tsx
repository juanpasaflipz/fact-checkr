'use client';

import { useState, useEffect, useRef, use } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import Sidebar from '@/components/features/layout/Sidebar';
import Header from '@/components/features/layout/Header';
import { api } from '@/lib/api-client';

interface WhatsAppMessage {
    id: number;
    wa_message_id: string;
    message_type: string;
    content: string;
    status: string;
    created_at: string;
}

interface WhatsAppUser {
    id: number;
    phone_hash: string;
    created_at: string;
}

export default function WhatsAppChatPage() {
    const router = useRouter();
    const params = useParams();
    const userId = params.userId as string;

    const [messages, setMessages] = useState<WhatsAppMessage[]>([]);
    const [user, setUser] = useState<WhatsAppUser | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (userId) {
            fetchData();
        }
    }, [userId]);

    // Scroll to bottom when messages load
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const fetchData = async () => {
        try {
            setLoading(true);
            // Fetch user and messages in parallel
            const [userData, messagesData] = await Promise.all([
                api.get<WhatsAppUser>(`/api/whatsapp/users/${userId}`),
                api.get<WhatsAppMessage[]>(`/api/whatsapp/messages/${userId}`)
            ]);

            setUser(userData);
            // Backend returns messages descending (newest first), reverse to show chronologically
            setMessages([...messagesData].reverse());
            setError(null);
        } catch (err: any) {
            console.error('Error fetching chat data:', err);
            setError('Error al cargar la conversación');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Sidebar />
            <div className="lg:pl-64 flex flex-col h-screen">
                <Header
                    searchQuery=""
                    setSearchQuery={() => { }}
                    onSearch={() => { }}
                />

                <main className="flex-1 p-4 md:p-6 overflow-hidden flex flex-col">
                    {/* Breadcrumb / Header */}
                    <div className="mb-4 flex items-center gap-4">
                        <Link href="/admin/whatsapp" className="text-gray-500 hover:text-gray-700">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </Link>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">
                                {user ? `Chat #${user.id}` : 'Cargando...'}
                            </h1>
                            {user && (
                                <p className="text-xs text-gray-500 font-mono">
                                    ID: {user.phone_hash.substring(0, 15)}...
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Chat Area */}
                    <div className="flex-1 bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex flex-col relative">

                        {/* Messages List */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
                            {loading ? (
                                <div className="flex justify-center items-center h-full">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                                </div>
                            ) : error ? (
                                <div className="flex justify-center items-center h-full text-red-500">
                                    {error}
                                </div>
                            ) : messages.length === 0 ? (
                                <div className="flex justify-center items-center h-full text-gray-400">
                                    No hay mensajes en esta conversación.
                                </div>
                            ) : (
                                messages.map((msg) => {
                                    const isReceived = msg.status === 'received';

                                    return (
                                        <div
                                            key={msg.id}
                                            className={`flex w-full ${isReceived ? 'justify-start' : 'justify-end'}`}
                                        >
                                            <div className={`
                                        max-w-[70%] rounded-lg px-4 py-2 shadow-sm
                                        ${isReceived
                                                    ? 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'
                                                    : 'bg-indigo-600 text-white rounded-tr-none'
                                                }
                                    `}>
                                                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                                                <div className={`text-[10px] mt-1 text-right ${isReceived ? 'text-gray-400' : 'text-indigo-200'}`}>
                                                    {new Date(msg.created_at).toLocaleString()}
                                                    {msg.status !== 'received' && ` • ${msg.status}`}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Read-Only Input Area */}
                        <div className="p-4 bg-white border-t border-gray-200">
                            <div className="relative">
                                <input
                                    type="text"
                                    disabled
                                    placeholder="El envío de respuestas está deshabilitado (Modo Solo Lectura)"
                                    className="w-full pl-4 pr-12 py-3 bg-gray-100 border border-gray-200 rounded-lg text-gray-500 focus:outline-none cursor-not-allowed"
                                />
                                <div className="absolute right-3 top-3 text-gray-400">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                    </svg>
                                </div>
                            </div>
                            <p className="text-xs text-gray-400 mt-2 text-center">
                                Para responder, se requiere acceso al número de teléfono desencriptado.
                            </p>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

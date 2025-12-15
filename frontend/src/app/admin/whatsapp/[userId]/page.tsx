'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface Message {
    id: number;
    content: string;
    status: string;
    created_at: string;
    message_type: string;
}

interface User {
    id: number;
    phone_hash: string;
    locale: string;
}

export default function WhatsAppChatView() {
    const params = useParams();
    const router = useRouter();
    const userId = params.userId;

    const [user, setUser] = useState<User | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [newMessage, setNewMessage] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (userId) {
            fetchData();
        }
    }, [userId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const fetchData = async () => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

            const [userRes, messagesRes] = await Promise.all([
                fetch(`${API_URL}/whatsapp/users/${userId}`),
                fetch(`${API_URL}/whatsapp/messages/${userId}`)
            ]);

            if (!userRes.ok || !messagesRes.ok) throw new Error('Failed to fetch data');

            const userData = await userRes.json();
            const messagesData = await messagesRes.json();

            setUser(userData);
            // Messages come in descending order (newest first), reverse for chat view
            setMessages(messagesData.reverse());
        } catch (error) {
            console.error('Error fetching chat data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim()) return;

        setSending(true);
        try {
            // Note: This endpoint expects a phone number, but we only have a hash.
            // In a real scenario, we'd need a way to look up the number or send via ID if supported.
            // For now, this UI assumes the backend might handle it or it's a placeholder for future implementation.
            // IMPORTANT: The current backend /send endpoint takes 'to' (phone number).
            // Since we don't store the raw phone number, we can't actually send a message back easily
            // without changing the backend to store numbers or having a lookup.
            // For this task, we'll implement the UI logic but note this limitation.

            // Temporary: Simulate sending for UI demonstration
            const simulatedMsg: Message = {
                id: Date.now(),
                content: newMessage,
                status: 'sent',
                created_at: new Date().toISOString(),
                message_type: 'text'
            };

            setMessages([...messages, simulatedMsg]);
            setNewMessage('');
        } catch (error) {
            console.error('Error sending message:', error);
        } finally {
            setSending(false);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center p-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    if (!user) {
        return <div className="p-8 text-red-600">User not found</div>;
    }

    return (
        <div className="flex flex-col h-[calc(100vh-64px)] bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div>
                    <h1 className="text-lg font-bold text-gray-900">Chat with User #{user.id}</h1>
                    <p className="text-sm text-gray-500 font-mono">Hash: {user.phone_hash.substring(0, 12)}...</p>
                </div>
                <button
                    onClick={() => router.back()}
                    className="text-gray-600 hover:text-gray-900 text-sm font-medium"
                >
                    Back to List
                </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((msg) => {
                    const isReceived = msg.status === 'received';
                    return (
                        <div
                            key={msg.id}
                            className={`flex ${isReceived ? 'justify-start' : 'justify-end'}`}
                        >
                            <div
                                className={`max-w-[70%] rounded-lg px-4 py-2 shadow-sm ${isReceived
                                        ? 'bg-white text-gray-900 border border-gray-200'
                                        : 'bg-indigo-600 text-white'
                                    }`}
                            >
                                <div className="text-sm">{msg.content}</div>
                                <div className={`text-[10px] mt-1 ${isReceived ? 'text-gray-500' : 'text-indigo-200'} text-right`}>
                                    {format(new Date(msg.created_at), 'p', { locale: es })}
                                </div>
                            </div>
                        </div>
                    );
                })}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-gray-200 p-4">
                <form onSubmit={handleSend} className="flex gap-4 max-w-4xl mx-auto">
                    <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Type a message..."
                        className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-black placeholder:text-gray-400"
                        disabled={sending}
                    />
                    <button
                        type="submit"
                        disabled={sending || !newMessage.trim()}
                        className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {sending ? 'Sending...' : 'Send'}
                    </button>
                </form>
            </div>
        </div>
    );
}

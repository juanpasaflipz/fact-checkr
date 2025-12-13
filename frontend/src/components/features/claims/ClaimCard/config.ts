import { VerificationStatus } from './types';

export const statusConfig: Record<VerificationStatus, {
    label: string;
    icon: string;
    badge: string;
    accent: string;
    color: string;
}> = {
    Verified: {
        label: 'Verificado',
        icon: 'ShieldCheck',
        badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        accent: 'border-l-emerald-500',
        color: 'emerald',
    },
    Debunked: {
        label: 'Falso',
        icon: 'ShieldAlert',
        badge: 'bg-rose-50 text-rose-700 border-rose-200',
        accent: 'border-l-rose-500',
        color: 'rose',
    },
    Misleading: {
        label: 'Engañoso',
        icon: 'AlertTriangle',
        badge: 'bg-amber-50 text-amber-700 border-amber-200',
        accent: 'border-l-amber-500',
        color: 'amber',
    },
    Unverified: {
        label: 'Sin Verificar',
        icon: 'Clock',
        badge: 'bg-blue-50 text-blue-700 border-blue-200',
        accent: 'border-l-blue-500',
        color: 'blue',
    },
};

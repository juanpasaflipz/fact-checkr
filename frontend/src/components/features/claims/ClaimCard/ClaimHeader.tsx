import React from 'react';
import { ClaimProps } from './types';
import { statusConfig } from './config';
import { Icon } from './Icons';

export function ClaimHeader({ claim }: ClaimProps) {
    const status = claim.verification?.status || "Unverified";
    const config = statusConfig[status];

    return (
        <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="
          size-10 rounded-lg 
          bg-gray-100 
          flex items-center justify-center flex-shrink-0
          border border-gray-200
          group-hover:bg-gray-200 transition-colors duration-200
        ">
                    <svg className="size-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                </div>
                <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-900 truncate font-semibold">
                        {claim.source_post?.author || "Desconocido"}
                    </p>
                    <p className="text-xs text-gray-500">{claim.source_post?.platform || "Unknown"}</p>
                </div>
            </div>

            <span className={`
        inline-flex items-center gap-1.5 px-3 py-1.5 
        rounded-lg text-xs font-semibold border 
        ${config.badge} 
        transition-all duration-200
      `}>
                <Icon name={config.icon} className="size-4" />
                {config.label}
            </span>
        </div>
    );
}

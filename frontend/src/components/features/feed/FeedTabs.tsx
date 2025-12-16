import React from "react";

interface FeedTabsProps {
    activeTab: string;
    onTabChange: (tabId: string) => void;
}

const tabs = [
    { id: "todos", label: "Todos" },
    { id: "verificados", label: "Verificados" },
    { id: "falsos", label: "Falsos" },
    { id: "sin-verificar", label: "Sin verificar" },
];

export default function FeedTabs({ activeTab, onTabChange }: FeedTabsProps) {
    return (
        <div className="relative">
            <div className="flex gap-2 sm:gap-3 overflow-x-auto pb-1 scrollbar-hide">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        type="button"
                        onClick={() => onTabChange(tab.id)}
                        className={`
                relative flex-shrink-0 px-3 sm:px-5 py-2 sm:py-2.5 rounded-lg 
                text-xs sm:text-sm transition-all duration-200 whitespace-nowrap font-semibold
                border touch-manipulation cursor-pointer
                ${activeTab === tab.id
                                ? 'bg-gray-900 border-gray-900 text-white'
                                : 'border-transparent text-gray-600 active:bg-gray-100 active:text-gray-900'
                            }
                hover:bg-gray-100 hover:text-gray-900
              `}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>
        </div>
    );
}

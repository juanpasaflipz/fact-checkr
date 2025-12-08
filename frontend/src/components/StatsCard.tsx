import React from 'react';

interface StatsCardProps {
  title: string;
  value: string | number;
  trend?: string;
  trendUp?: boolean;
  icon: string;
  color: "blue" | "emerald" | "rose" | "amber";
}

export default function StatsCard({ title, value, trend, trendUp, icon, color }: StatsCardProps) {
  const colorStyles = {
    blue: { 
      bg: "bg-blue-50",
      border: "border-blue-200",
      text: "text-blue-700",
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600"
    },
    emerald: { 
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      text: "text-emerald-700",
      iconBg: "bg-emerald-100",
      iconColor: "text-emerald-600"
    },
    rose: { 
      bg: "bg-rose-50",
      border: "border-rose-200",
      text: "text-rose-700",
      iconBg: "bg-rose-100",
      iconColor: "text-rose-600"
    },
    amber: { 
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-700",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600"
    },
  };

  const style = colorStyles[color];

  return (
    <div className={`
      group relative bg-white rounded-lg p-6 
      border border-gray-200
      transition-all duration-200 
      hover:shadow-sm hover:border-gray-300
    `}>
      <div className="flex items-start justify-between mb-4">
        <div className={`
          p-3 rounded-lg 
          bg-gray-100
          text-gray-700
          transition-colors duration-200
        `}>
          <Icon name={icon} className="size-6" />
        </div>
        {trend && (
          <div className={`
            flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold
            bg-gray-100 text-gray-700 border border-gray-200
          `}>
            <TrendIcon up={trendUp} className="size-3.5" />
          </div>
        )}
      </div>
      
      <h3 className={`text-3xl mb-1.5 font-bold tracking-tight text-gray-900 transition-colors`}>
        {value}
      </h3>
      <p className="text-sm text-gray-600 mb-2 font-medium">{title}</p>
      {trend && (
        <p className={`text-xs font-medium text-gray-600`}>
          {trend}
        </p>
      )}
    </div>
  );
}

function Icon({ name, className }: { name: string; className?: string }) {
  switch (name) {
    case "DocumentSearch":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>;
    case "ShieldCheck":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
    case "AlertTriangle":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>;
    case "Activity":
      return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>;
    default:
      return null;
  }
}

function TrendIcon({ up, className }: { up?: boolean; className?: string }) {
  if (up) {
    return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>;
  }
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>;
}

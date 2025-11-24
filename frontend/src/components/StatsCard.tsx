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
    blue: { bg: "bg-blue-50", iconColor: "text-blue-600", gradient: "from-blue-500 to-blue-600" },
    emerald: { bg: "bg-green-50", iconColor: "text-green-600", gradient: "from-green-500 to-green-600" },
    rose: { bg: "bg-red-50", iconColor: "text-red-600", gradient: "from-red-500 to-red-600" },
    amber: { bg: "bg-orange-50", iconColor: "text-orange-600", gradient: "from-orange-500 to-orange-600" },
  };

  const style = colorStyles[color];

  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-100">
      <div className="flex items-start justify-between mb-4">
        <div className={`${style.bg} p-3 rounded-xl`}>
          <Icon name={icon} className={`size-6 ${style.iconColor}`} />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
            trendUp 
              ? 'bg-green-50 text-green-700' 
              : 'bg-red-50 text-red-700'
          }`}>
            <TrendIcon up={trendUp} className="size-3" />
          </div>
        )}
      </div>
      
      <h3 className="text-3xl text-gray-900 mb-1 font-bold">{value}</h3>
      <p className="text-sm text-gray-500 mb-2 font-medium">{title}</p>
      {trend && (
        <p className={`text-xs ${trendUp ? 'text-green-600' : 'text-red-600'} font-medium`}>
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

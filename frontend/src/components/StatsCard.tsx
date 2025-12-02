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
      neon: "#00f0ff",
      bg: "bg-[#111118]",
      border: "border-[#00f0ff]",
      text: "text-[#00f0ff]",
      glow: "glow-cyan"
    },
    emerald: { 
      neon: "#00ff88",
      bg: "bg-[#111118]",
      border: "border-[#00ff88]",
      text: "text-[#00ff88]",
      glow: "glow-green"
    },
    rose: { 
      neon: "#ff00ff",
      bg: "bg-[#111118]",
      border: "border-[#ff00ff]",
      text: "text-[#ff00ff]",
      glow: "glow-pink"
    },
    amber: { 
      neon: "#ffaa00",
      bg: "bg-[#111118]",
      border: "border-[#ffaa00]",
      text: "text-[#ffaa00]",
      glow: "glow-cyan"
    },
  };

  const style = colorStyles[color];

  return (
    <div className={`
      group relative ${style.bg} rounded-lg p-6 
      border-2 ${style.border}
      ${style.glow}
      transition-all duration-300 
      hover:-translate-y-1 hover:scale-[1.02]
      overflow-hidden
      before:absolute before:inset-0 before:bg-gradient-to-br before:from-transparent before:via-transparent before:to-[${style.neon}]/5
      before:opacity-0 group-hover:before:opacity-100 before:transition-opacity before:duration-300
    `}
    style={{
      boxShadow: `0 0 20px ${style.neon}40, inset 0 0 20px ${style.neon}10`
    }}>
      {/* Grid pattern overlay */}
      <div className="absolute inset-0 opacity-10" style={{
        backgroundImage: `
          linear-gradient(${style.neon}40 1px, transparent 1px),
          linear-gradient(90deg, ${style.neon}40 1px, transparent 1px)
        `,
        backgroundSize: '20px 20px'
      }} />
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className={`
            p-3.5 rounded-lg 
            border-2 ${style.border}
            ${style.glow}
            group-hover:scale-110 
            transition-transform duration-300
            bg-[#1a1a24]
          `}
          style={{
            boxShadow: `0 0 15px ${style.neon}60`
          }}>
            <Icon name={icon} className={`size-6 ${style.text}`} style={{
              filter: `drop-shadow(0 0 5px ${style.neon})`
            }} />
          </div>
          {trend && (
            <div className={`
              flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold
              ${trendUp 
                ? 'bg-[#1a1a24] border-2 border-[#00ff88] text-[#00ff88]' 
                : 'bg-[#1a1a24] border-2 border-[#ff00ff] text-[#ff00ff]'
              }
            `}
            style={{
              boxShadow: trendUp 
                ? '0 0 10px rgba(0, 255, 136, 0.5)'
                : '0 0 10px rgba(255, 0, 255, 0.5)'
            }}>
              <TrendIcon up={trendUp} className="size-3.5" />
            </div>
          )}
        </div>
        
        <h3 className={`text-3xl mb-1.5 font-bold tracking-tight ${style.text} transition-colors`}
            style={{
              textShadow: `0 0 10px ${style.neon}, 0 0 20px ${style.neon}80`
            }}>
          {value}
        </h3>
        <p className="text-sm text-gray-400 mb-2 font-semibold">{title}</p>
        {trend && (
          <p className={`text-xs font-bold ${trendUp ? 'text-[#00ff88]' : 'text-[#ff00ff]'}`}
             style={{
               textShadow: trendUp 
                 ? '0 0 5px #00ff88'
                 : '0 0 5px #ff00ff'
             }}>
            {trend}
          </p>
        )}
      </div>
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

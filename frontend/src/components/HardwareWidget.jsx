import React, { useState } from 'react';
import { Cpu, Zap, Activity, HardDrive, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

export default function HardwareWidget({ systemInfo }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [copied, setCopied] = useState(false);

  const gpuName = systemInfo?.gpu_name || 'GPU';
  const gpuUtil = systemInfo?.gpu_util_percent || 0;
  const gpuTemp = systemInfo?.gpu_temp_c || 0;
  const vramUsed = systemInfo?.gpu_vram_used_gb || '0.0';
  const vramTotal = systemInfo?.gpu_vram_total_gb || '0.0';
  const vramPct = systemInfo?.gpu_vram_percent || 0;
  const powerDraw = systemInfo?.power_draw_w || 0;
  const powerLimit = systemInfo?.power_limit_w || 0;
  const powerPct = systemInfo?.power_percent || 0;
  const ramUsed = systemInfo?.ram_used_gb || '0.0';
  const ramTotal = systemInfo?.ram_total_gb || '0.0';
  const ramPct = systemInfo?.ram_percent || 0;
  const cpuUtil = systemInfo?.cpu_util_percent || 0;
  const engineMem = systemInfo?.engine_mem_gb || '0.1';

  const copySpecs = () => {
    const text = `${gpuName} | GPU: ${gpuUtil}% (${gpuTemp}°C) | VRAM: ${vramUsed}/${vramTotal} GB | RAM: ${ramUsed}/${ramTotal} GB | CPU: ${cpuUtil}%`;
    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed bottom-6 right-6 z-40 w-72 bg-white rounded-2xl shadow-xl border border-slate-200/90 overflow-hidden font-sans transition-all duration-200 hover:shadow-2xl">
      {/* Header matching user's widget */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-100 select-none">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-extrabold text-sm text-slate-900 tracking-tight">{gpuName}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={copySpecs}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
            title="Copy specs to clipboard"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
            title={isCollapsed ? "Expand monitor" : "Collapse monitor"}
          >
            {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="p-4 space-y-3.5 bg-white text-xs text-slate-700">
          {/* GPU Utilization */}
          <div className="space-y-1">
            <div className="flex justify-between font-medium">
              <span className="text-slate-500">GPU</span>
              <span className="font-mono text-slate-800 font-semibold">{gpuUtil}%</span>
            </div>
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(2, gpuUtil))}%` }}
              />
            </div>
          </div>

          {/* GPU Temp */}
          <div className="space-y-1">
            <div className="flex justify-between font-medium">
              <span className="text-slate-500">GPU Temp</span>
              <span className="font-mono text-emerald-600 font-semibold">{gpuTemp}°C</span>
            </div>
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-emerald-400 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, (gpuTemp / 90) * 100)}%` }}
              />
            </div>
          </div>

          {/* VRAM */}
          <div className="space-y-1">
            <div className="flex justify-between font-medium">
              <span className="text-slate-500">VRAM</span>
              <span className="font-mono text-slate-800 font-semibold">{vramUsed} GB / {vramTotal} GB</span>
            </div>
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-cyan-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(2, vramPct))}%` }}
              />
            </div>
          </div>

          {/* Power */}
          {powerLimit > 0 && (
            <div className="space-y-1">
              <div className="flex justify-between font-medium">
                <span className="text-slate-500">Power</span>
                <span className="font-mono text-slate-800 font-semibold">{powerDraw} / {powerLimit} W</span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(100, Math.max(2, powerPct))}%` }}
                />
              </div>
            </div>
          )}

          {/* RAM */}
          <div className="space-y-1">
            <div className="flex justify-between font-medium">
              <span className="text-slate-500">RAM</span>
              <span className="font-mono text-slate-800 font-semibold">{ramUsed} GB / {ramTotal} GB</span>
            </div>
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-purple-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(2, ramPct))}%` }}
              />
            </div>
          </div>

          {/* CPU */}
          <div className="space-y-1">
            <div className="flex justify-between font-medium">
              <span className="text-slate-500">CPU</span>
              <span className="font-mono text-slate-800 font-semibold">{cpuUtil}%</span>
            </div>
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-blue-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(2, cpuUtil))}%` }}
              />
            </div>
          </div>

          {/* Engine Memory & Status */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Engine</span>
            <span className="font-mono text-slate-800 font-medium">{engineMem} GB</span>
          </div>

          <div className="flex items-center gap-2 pt-1 text-[11px] text-emerald-600 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>Audio engine reachable</span>
          </div>
        </div>
      )}
    </div>
  );
}


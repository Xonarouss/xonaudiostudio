import React from 'react';
import { Cpu, Zap, Activity, HardDrive } from 'lucide-react';

export default function Footer({ systemInfo }) {
  const gpuName = systemInfo?.gpu_name || 'GPU';
  const vramUsed = systemInfo?.gpu_vram_used_gb || '0.0';
  const vramTotal = systemInfo?.gpu_vram_total_gb || '0.0';
  const ramUsed = systemInfo?.ram_used_gb || '0.0';
  const ramTotal = systemInfo?.ram_total_gb || '0.0';
  const cpuUtil = systemInfo?.cpu_util_percent || 0;
  const diskFree = systemInfo?.disk_free_gb || '0.0';

  return (
    <footer className="mt-auto border-t border-slate-200/90 bg-white/95 backdrop-blur-md py-5 px-6 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-600">
        {/* Left: Dynamic Real Hardware Specs */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 shadow-xs">
            <Cpu className="w-3.5 h-3.5 text-cyan-600" />
            <span className="font-semibold">{gpuName}</span>
            <span className="font-mono text-slate-500">({vramUsed}/{vramTotal} GB)</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 shadow-xs">
            <Zap className="w-3.5 h-3.5 text-purple-600" />
            <span>RAM</span>
            <span className="font-mono text-slate-500">({ramUsed}/{ramTotal} GB)</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 shadow-xs">
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            <span>CPU</span>
            <span className="font-mono text-slate-500">({cpuUtil}%)</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>CUDA Accelerated</span>
          </div>
        </div>

        {/* Center / Right: Mandatory Xonarous Inc Branding */}
        <div className="flex items-center gap-2 text-sm font-medium">
          <span className="text-slate-500">Built by</span>
          <a
            href="https://xonarous.nl"
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-600 hover:text-cyan-700 font-semibold tracking-wide hover:underline decoration-cyan-500/50 underline-offset-4 transition-all duration-200"
          >
            Xonarous Inc
          </a>
        </div>
      </div>
    </footer>
  );
}

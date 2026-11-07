import React from 'react';
import { Cpu, Zap, ShieldCheck } from 'lucide-react';

export default function Footer({ systemInfo }) {
  return (
    <footer className="mt-auto border-t border-slate-800/80 bg-studio-950/80 backdrop-blur-md py-6 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400">
        {/* Left: Branding & Hardware Specs */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-studio-900 border border-slate-800 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-mono">RTX 5080 (16GB VRAM)</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-studio-900 border border-slate-800 text-slate-300">
            <Zap className="w-3.5 h-3.5 text-purple-400" />
            <span className="font-mono">Ryzen 7 7800X3D</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-studio-900 border border-slate-800 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>CUDA Accelerated</span>
          </div>
        </div>

        {/* Center / Right: Mandatory Xonarous Inc Branding */}
        <div className="flex items-center gap-2 text-sm font-medium">
          <span className="text-slate-400">Built by</span>
          <a
            href="https://xonarous.nl"
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 font-semibold tracking-wide hover:underline decoration-cyan-400/50 underline-offset-4 transition-all duration-200"
          >
            Xonarous Inc
          </a>
        </div>
      </div>
    </footer>
  );
}


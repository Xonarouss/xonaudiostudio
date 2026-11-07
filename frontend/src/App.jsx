import React, { useState, useEffect } from 'react';
import { Mic, Radio, HardDrive, Volume2, Sparkles, RefreshCw } from 'lucide-react';
import VoiceLab from './components/VoiceLab';
import SoundStudio from './components/SoundStudio';
import ModelManager from './components/ModelManager';
import HardwareWidget from './components/HardwareWidget';
import Footer from './components/Footer';

export default function App() {
  const [activeTab, setActiveTab] = useState('voicelab'); // 'voicelab' | 'soundstudio' | 'models'
  const [modelsStatus, setModelsStatus] = useState({
    f5_tts: { installed: false, size_gb: '0.00' },
    stable_audio: { installed: false, size_gb: '0.00' }
  });
  const [systemInfo, setSystemInfo] = useState({
    gpu_name: 'GPU',
    gpu_util_percent: 0,
    gpu_temp_c: 0,
    gpu_vram_used_gb: '0.0',
    gpu_vram_total_gb: '0.0',
    gpu_vram_percent: 0,
    power_draw_w: 0,
    power_limit_w: 0,
    power_percent: 0,
    cpu_util_percent: 0,
    ram_used_gb: '0.0',
    ram_total_gb: '0.0',
    ram_percent: 0,
    engine_mem_gb: '0.1',
    disk_free_gb: '0.0',
    engine_status: 'Engine Online'
  });
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);

  const fetchStatus = async () => {
    setIsLoadingStatus(true);
    try {
      const [resModels, resSystem] = await Promise.all([
        fetch('/api/models/status').catch(() => null),
        fetch('/api/system/status').catch(() => null)
      ]);

      if (resModels && resModels.ok) {
        const data = await resModels.json();
        setModelsStatus(data);
      }
      if (resSystem && resSystem.ok) {
        const data = await resSystem.json();
        setSystemInfo(data);
      }
    } catch (err) {
      console.warn('Could not fetch status:', err);
    } finally {
      setIsLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000); // 3s interval for responsive hardware monitor
    return () => clearInterval(interval);
  }, []);

  const gpuName = systemInfo?.gpu_name || 'GPU';
  const vramUsed = systemInfo?.gpu_vram_used_gb || '0';
  const vramTotal = systemInfo?.gpu_vram_total_gb || '0';

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 light-mesh selection:bg-cyan-500 selection:text-white">
      {/* Top Navbar in Crisp White */}
      <header className="sticky top-0 z-30 border-b border-slate-200/90 bg-white/95 backdrop-blur-xl shadow-xs">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          {/* Logo & Brand Title */}
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-purple-600 p-[1.5px] shadow-sm flex-shrink-0">
              <div className="w-full h-full bg-white rounded-2xl flex items-center justify-center p-2">
                <Volume2 className="w-6 h-6 text-cyan-600" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold tracking-tight text-slate-900 font-sans">
                  XONAUDIO STUDIO
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-100 text-cyan-800 border border-cyan-200">
                  OPEN SOURCE
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">
                Neural Voice Cloning &amp; Foley Diffusion Workstation
              </p>
            </div>
          </div>

          {/* Navigation Tabs (White Mode) */}
          <div className="flex items-center bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200">
            <button
              onClick={() => setActiveTab('voicelab')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
                activeTab === 'voicelab'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <Mic className="w-4 h-4" />
              <span>Voice Lab</span>
            </button>

            <button
              onClick={() => setActiveTab('soundstudio')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
                activeTab === 'soundstudio'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <Radio className="w-4 h-4" />
              <span>Sound Studio</span>
            </button>

            <button
              onClick={() => setActiveTab('models')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
                activeTab === 'models'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <HardDrive className="w-4 h-4" />
              <span>Model Manager</span>
            </button>
          </div>

          {/* Dynamic Hardware Quick-Indicator in Header */}
          <div className="hidden lg:flex items-center gap-3">
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-100 border border-slate-200 text-xs shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-slate-700 font-semibold">{gpuName}</span>
              <span className="text-cyan-700 font-mono font-bold">
                {vramUsed} / {vramTotal} GB
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Studio Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {activeTab === 'voicelab' && (
          <VoiceLab
            modelsStatus={modelsStatus}
            onOpenModelManager={() => setActiveTab('models')}
          />
        )}

        {activeTab === 'soundstudio' && (
          <SoundStudio
            modelsStatus={modelsStatus}
            onOpenModelManager={() => setActiveTab('models')}
          />
        )}

        {activeTab === 'models' && (
          <ModelManager
            modelsStatus={modelsStatus}
            systemInfo={systemInfo}
            onRefresh={fetchStatus}
            isLoading={isLoadingStatus}
          />
        )}
      </main>

      {/* Floating Dynamic Hardware Monitor matching user's image */}
      <HardwareWidget systemInfo={systemInfo} />

      {/* Footer with Dynamic Hardware Specs and Xonarous Inc Link */}
      <Footer systemInfo={systemInfo} />
    </div>
  );
}

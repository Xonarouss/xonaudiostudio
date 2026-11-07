import React, { useState, useEffect } from 'react';
import { Mic, Radio, HardDrive, Settings, Volume2, Cpu, Sparkles, RefreshCw } from 'lucide-react';
import VoiceLab from './components/VoiceLab';
import SoundStudio from './components/SoundStudio';
import ModelManager from './components/ModelManager';
import Footer from './components/Footer';

export default function App() {
  const [activeTab, setActiveTab] = useState('voicelab'); // 'voicelab' | 'soundstudio' | 'models'
  const [modelsStatus, setModelsStatus] = useState({
    f5_tts: { installed: false, size_gb: '0.00' },
    stable_audio: { installed: false, size_gb: '0.00' }
  });
  const [systemInfo, setSystemInfo] = useState({
    gpu_name: 'NVIDIA GeForce RTX 5080',
    gpu_vram_used_gb: '1.2',
    gpu_vram_total_gb: '16.0',
    ram_used_gb: '12.4',
    ram_total_gb: '64.0',
    disk_free_gb: '512'
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
    const interval = setInterval(fetchStatus, 15000); // refresh every 15s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-studio-950 text-slate-100 gradient-mesh selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-studio-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-purple-600 p-[1.5px] shadow-glow-cyan">
              <div className="w-full h-full bg-studio-950 rounded-2xl flex items-center justify-center">
                <Volume2 className="w-6 h-6 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold tracking-tight text-white font-sans">
                  AI AUDIO STUDIO
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  PRO
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium">
                F5-TTS Voice Cloning &amp; Stable Audio Open Foley
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center bg-studio-900/90 p-1.5 rounded-2xl border border-slate-800">
            <button
              onClick={() => setActiveTab('voicelab')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
                activeTab === 'voicelab'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-glow-cyan'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-studio-800/50'
              }`}
            >
              <Mic className="w-4 h-4" />
              <span>Voice Lab</span>
            </button>

            <button
              onClick={() => setActiveTab('soundstudio')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
                activeTab === 'soundstudio'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-glow-purple'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-studio-800/50'
              }`}
            >
              <Radio className="w-4 h-4" />
              <span>Sound Studio</span>
            </button>

            <button
              onClick={() => setActiveTab('models')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
                activeTab === 'models'
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-glow-emerald'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-studio-800/50'
              }`}
            >
              <HardDrive className="w-4 h-4" />
              <span>Model Manager</span>
            </button>
          </div>

          {/* Hardware Quick-Indicator */}
          <div className="hidden lg:flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-studio-900 border border-slate-800 text-xs">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="text-slate-300 font-mono">RTX 5080</span>
              <span className="text-cyan-400 font-mono font-semibold">
                {systemInfo?.gpu_vram_used_gb || '0'} / 16GB
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main App Workspace */}
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

      {/* Footer Branding */}
      <Footer systemInfo={systemInfo} />
    </div>
  );
}


import React, { useState, useEffect } from 'react';
import { Play, Download, Trash2, Music, Mic, Clock, RefreshCw, FolderOpen, ArrowUpRight, Sparkles, Music2, Disc, User, MapPin } from 'lucide-react';
import AudioPlayer from './AudioPlayer';

export default function GenerationsLibrary({ onLoadIntoStudio, userProfile }) {
  const [generations, setGenerations] = useState([]);
  const [selectedAudio, setSelectedAudio] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all' | 'tts' | 'sfx' | 'song_cover'
  const [isLoading, setIsLoading] = useState(false);

  const fetchGenerations = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/generations');
      if (res.ok) {
        const data = await res.json();
        setGenerations(data);
        if (data.length > 0 && !selectedAudio) {
          setSelectedAudio(data[0]);
        }
      }
    } catch (e) {
      console.warn("Could not fetch generations:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGenerations();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this audio generation?")) return;
    try {
      const res = await fetch(`/api/generations/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setGenerations(prev => prev.filter(g => g.id !== id));
        if (selectedAudio?.id === id) {
          setSelectedAudio(null);
        }
      }
    } catch (err) {
      console.warn("Delete error:", err);
    }
  };

  const filtered = generations.filter(g => {
    if (filter === 'all') return true;
    return g.type === filter;
  });

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-white rounded-2xl border border-slate-200/90 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-cyan-100 text-cyan-800 border border-cyan-200">
              Audio Archive
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <FolderOpen className="w-6 h-6 text-cyan-600" />
            Previous Generations &amp; Library
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse, play, re-load, and export all generated voice clips and sound effects.
          </p>
        </div>

        {/* Filter buttons & Refresh */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs flex-wrap gap-1">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                filter === 'all' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All ({generations.length})
            </button>
            <button
              onClick={() => setFilter('song_cover')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                filter === 'song_cover' ? 'bg-white text-pink-700 shadow-2xs font-bold' : 'text-slate-600 hover:text-pink-600'
              }`}
            >
              Song Covers ({generations.filter(g => g.type === 'song_cover').length})
            </button>
            <button
              onClick={() => setFilter('tts')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                filter === 'tts' ? 'bg-white text-cyan-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Voice ({generations.filter(g => g.type === 'tts').length})
            </button>
            <button
              onClick={() => setFilter('sfx')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                filter === 'sfx' ? 'bg-white text-purple-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              SFX ({generations.filter(g => g.type === 'sfx').length})
            </button>
          </div>

          <button
            onClick={fetchGenerations}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors shadow-2xs"
            title="Refresh library"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Active Audio Player Preview */}
      {selectedAudio && (
        <div className="space-y-2">
          <AudioPlayer
            audioUrl={selectedAudio.url}
            title={selectedAudio.title}
            subtitle={`${
              selectedAudio.type === 'song_cover'
                ? 'AI Song Cover Lab (BS-RoFormer + RVC v2)'
                : selectedAudio.type === 'tts'
                ? 'Voice Lab Speech'
                : 'SFX Studio Foley'
            } • ${selectedAudio.created_at} • ${selectedAudio.size_mb} MB`}
          />
        </div>
      )}

      {/* Grid of Generations Cards */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((item) => {
            const isSelected = selectedAudio?.id === item.id;
            const isSongCover = item.type === 'song_cover';
            const isTTS = item.type === 'tts';

            return (
              <div
                key={item.id}
                onClick={() => setSelectedAudio(item)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all hover:shadow-md flex flex-col justify-between space-y-3 bg-white ${
                  isSelected
                    ? isSongCover
                      ? 'border-pink-500 ring-2 ring-pink-500/20 shadow-sm'
                      : 'border-cyan-500 ring-2 ring-cyan-500/20 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-bold flex items-center gap-1 ${
                        isSongCover
                          ? 'bg-pink-50 text-pink-700 border border-pink-200'
                          : isTTS
                          ? 'bg-cyan-50 text-cyan-700 border border-cyan-200'
                          : 'bg-purple-50 text-purple-700 border border-purple-200'
                      }`}
                    >
                      {isSongCover ? (
                        <Music2 className="w-3 h-3 text-pink-600" />
                      ) : isTTS ? (
                        <Mic className="w-3 h-3" />
                      ) : (
                        <Music className="w-3 h-3" />
                      )}
                      {isSongCover ? 'Song Cover' : isTTS ? 'Voice Lab' : 'SFX Studio'}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">{item.created_at}</span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-800 truncate" title={item.filename}>
                    {item.title}
                  </h4>
                  {isSongCover && item.voice_title && (
                    <div className="flex items-center gap-1.5 pt-0.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-pink-50 text-pink-700 border border-pink-200">
                        <User className="w-2.5 h-2.5" />
                        {item.voice_title} Cover
                      </span>
                    </div>
                  )}
                  <p className="text-[11px] font-mono text-slate-500 truncate">
                    {item.filename}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-medium">
                    <MapPin className="w-2.5 h-2.5 text-rose-500 shrink-0" />
                    <span>{userProfile?.location || 'Kerkrade'}</span>
                    <span className="text-slate-300">•</span>
                    <span className="font-mono text-[11px] text-slate-400">{item.size_mb} MB</span>
                  </div>

                  <div className="flex items-center gap-1">
                    {onLoadIntoStudio && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onLoadIntoStudio(item);
                        }}
                        className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-cyan-700 transition-colors"
                        title="Load into Studio"
                      >
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                    <a
                      href={item.url}
                      download
                      onClick={(e) => e.stopPropagation()}
                      className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-emerald-700 transition-colors"
                      title="Download WAV"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                    <button
                      onClick={(e) => handleDelete(item.id, e)}
                      className="p-1.5 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"
                      title="Delete audio"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center flex flex-col items-center justify-center gap-3 shadow-xs">
          <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
            <Music className="w-7 h-7" />
          </div>
          <p className="text-sm font-bold text-slate-800">No audio generations found</p>
          <p className="text-xs text-slate-500 max-w-sm">
            Generate your first voice clip in Voice Lab or sound effect in Sound Studio. They will be archived here automatically.
          </p>
        </div>
      )}
    </div>
  );
}


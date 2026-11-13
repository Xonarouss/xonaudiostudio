import React, { useState, useRef } from 'react';
import { User, MapPin, Camera, X, Check, RotateCcw, Sparkles, ShieldCheck } from 'lucide-react';

const PRESET_AVATARS = [
  { id: 'avatar-chris', name: 'Studio Engineer (Chris)', src: '/avatars/avatar-chris.svg' },
  { id: 'avatar-studio', name: 'Studio Microphone', src: '/avatars/avatar-studio.svg' },
  { id: 'avatar-neon', name: 'Neon Pulse Wave', src: '/avatars/avatar-neon.svg' },
  { id: 'avatar-producer', name: 'Vinyl Producer', src: '/avatars/avatar-producer.svg' }
];

export default function UserProfileModal({ isOpen, onClose, userProfile, onSaveProfile }) {
  if (!isOpen) return null;

  const [nickname, setNickname] = useState(userProfile?.nickname || 'Chris');
  const [location, setLocation] = useState(userProfile?.location || 'Kerkrade');
  const [bio, setBio] = useState(userProfile?.bio || 'Studio Director');
  const [selectedAvatar, setSelectedAvatar] = useState(userProfile?.avatar || 'avatar-chris');
  const [customAvatarData, setCustomAvatarData] = useState(userProfile?.custom_avatar_data || null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        alert('Image must be under 2MB');
        return;
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        setCustomAvatarData(event.target.result);
        setSelectedAvatar('custom');
      };
      reader.readAsDataURL(file);
    }
  };

  const getActiveAvatarSrc = () => {
    if (selectedAvatar === 'custom' && customAvatarData) {
      return customAvatarData;
    }
    const preset = PRESET_AVATARS.find(a => a.id === selectedAvatar);
    return preset ? preset.src : '/avatars/avatar-chris.svg';
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    const updated = {
      nickname: nickname.trim() || 'Chris',
      location: location.trim() || 'Kerkrade',
      bio: bio.trim() || 'Studio Director',
      avatar: selectedAvatar,
      custom_avatar_data: selectedAvatar === 'custom' ? customAvatarData : null
    };

    try {
      await onSaveProfile(updated);
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        onClose();
      }, 700);
    } catch (err) {
      console.error('Failed to save profile:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setNickname('Chris');
    setLocation('Kerkrade');
    setBio('Studio Director');
    setSelectedAvatar('avatar-chris');
    setCustomAvatarData(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fadeIn">
      <div 
        className="w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col font-sans"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-slate-50 via-cyan-50/40 to-blue-50/30 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 text-white flex items-center justify-center shadow-xs">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-slate-900 tracking-tight">Studio Identity &amp; Profile</h2>
              <p className="text-[11px] text-slate-500 font-medium">Nickname, Avatar &amp; Herkomst</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Live Profile Card Preview matching Chris's layout */}
        <div className="p-6 bg-gradient-to-b from-slate-50/80 to-white border-b border-slate-100 text-center flex flex-col items-center">
          {/* Top: Nickname */}
          <div className="mb-2">
            <span className="text-base font-extrabold text-slate-900 tracking-tight block">
              {nickname || 'Chris'}
            </span>
            <span className="text-[10px] font-semibold text-cyan-700 bg-cyan-100/80 px-2.5 py-0.5 rounded-full inline-block border border-cyan-200/60">
              {bio || 'Studio Director'}
            </span>
          </div>

          {/* Center: Avatar */}
          <div className="relative my-2 group">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 p-[2px] shadow-md">
              <div className="w-full h-full bg-slate-900 rounded-[22px] overflow-hidden flex items-center justify-center">
                <img 
                  src={getActiveAvatarSrc()} 
                  alt={nickname} 
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="absolute -bottom-1 -right-1 p-2 rounded-xl bg-cyan-600 hover:bg-cyan-700 text-white shadow-md transition-all active:scale-95"
              title="Upload custom image"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>

          {/* Bottom under Avatar: Naam van Herkomst */}
          <div className="mt-2 flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-white border border-slate-200/90 px-3 py-1 rounded-full shadow-2xs">
            <MapPin className="w-3.5 h-3.5 text-rose-500" />
            <span>{location || 'Kerkrade'}</span>
          </div>
        </div>

        {/* Edit Form */}
        <form onSubmit={handleSave} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Nickname / Roepnaam
            </label>
            <input
              type="text"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="e.g. Chris"
              className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600/30 text-slate-900 font-medium"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Naam van Herkomst (Woonplaats / Origin)
            </label>
            <div className="relative">
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Kerkrade"
                className="w-full pl-9 pr-3.5 py-2.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600/30 text-slate-900 font-medium"
                required
              />
              <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            </div>
          </div>

          {/* Avatar Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Kies Avatar
            </label>
            <div className="grid grid-cols-4 gap-2">
              {PRESET_AVATARS.map((av) => (
                <button
                  key={av.id}
                  type="button"
                  onClick={() => setSelectedAvatar(av.id)}
                  className={`p-1.5 rounded-2xl border-2 transition-all flex flex-col items-center ${
                    selectedAvatar === av.id
                      ? 'border-cyan-600 bg-cyan-50/40 shadow-xs'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                  title={av.name}
                >
                  <img src={av.src} alt={av.name} className="w-10 h-10 rounded-xl object-cover" />
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-500 hover:text-slate-800 rounded-xl hover:bg-slate-100 transition-colors"
              title="Reset to Chris - Kerkrade"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Annuleren
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center gap-1.5 px-5 py-2 text-xs font-extrabold text-white bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-xl shadow-md transition-all active:scale-95 disabled:opacity-50"
              >
                {saveSuccess ? (
                  <>
                    <Check className="w-4 h-4 text-white" />
                    <span>Opgeslagen!</span>
                  </>
                ) : (
                  <span>Opslaan</span>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

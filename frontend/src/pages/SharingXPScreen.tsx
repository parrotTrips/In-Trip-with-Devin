import TopBar from '../components/TopBar';
import { Camera, Music, FolderOpen, MessageCircle, Share2, ExternalLink, Heart, Users } from 'lucide-react';

const sharingItems = [
  {
    id: 'photos',
    title: 'Group Photos',
    description: 'Share and browse photos from the trip with everyone',
    icon: <Camera size={24} />,
    emoji: '📸',
    color: 'from-pink-500 to-rose-500',
    bgColor: 'bg-pink-50',
    textColor: 'text-pink-600',
    link: '', // placeholder - will be set by admin
    linkLabel: 'Open Album',
  },
  {
    id: 'spotify',
    title: 'Trip Playlist',
    description: 'Our shared Spotify playlist — add your favorite songs!',
    icon: <Music size={24} />,
    emoji: '🎵',
    color: 'from-green-500 to-emerald-500',
    bgColor: 'bg-green-50',
    textColor: 'text-green-600',
    link: '', // placeholder - will be set by admin
    linkLabel: 'Open on Spotify',
  },
  {
    id: 'drive',
    title: 'Shared Files',
    description: 'Upload and access documents, videos, and other files',
    icon: <FolderOpen size={24} />,
    emoji: '📂',
    color: 'from-blue-500 to-indigo-500',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600',
    link: '', // placeholder - will be set by admin
    linkLabel: 'Open Drive Folder',
  },
  {
    id: 'stories',
    title: 'Trip Stories',
    description: 'Share your favorite moments and stories from the trip',
    icon: <Heart size={24} />,
    emoji: '💬',
    color: 'from-purple-500 to-violet-500',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-600',
    link: '', // placeholder - will be set by admin
    linkLabel: 'Share a Story',
  },
  {
    id: 'group',
    title: 'WhatsApp Group',
    description: 'Stay connected with the group chat',
    icon: <MessageCircle size={24} />,
    emoji: '💬',
    color: 'from-emerald-500 to-teal-500',
    bgColor: 'bg-emerald-50',
    textColor: 'text-emerald-600',
    link: 'https://chat.whatsapp.com/KymXF54kl2jGX9fEntj5hB?mode=gi_t',
    linkLabel: 'Open WhatsApp',
  },
];

export default function SharingXPScreen() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 via-white to-pink-50 pb-20">
      <TopBar title="Sharing XP" />

      <div className="pt-14">
        {/* Header */}
        <div className="bg-gradient-to-br from-orange-500 via-pink-500 to-rose-500 px-5 py-6 text-white">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
              <Share2 size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold font-[Fredoka]">Sharing XP</h2>
              <p className="text-orange-100 text-sm">Connect, share, and relive the moments</p>
            </div>
          </div>

          {/* Stats */}
          <div className="flex gap-3 mt-4">
            <div className="flex-1 bg-white/10 rounded-xl p-3 text-center">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <Users size={14} />
                <span className="text-xs font-medium">Travelers</span>
              </div>
              <p className="text-lg font-bold">14</p>
            </div>
            <div className="flex-1 bg-white/10 rounded-xl p-3 text-center">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <Camera size={14} />
                <span className="text-xs font-medium">Photos</span>
              </div>
              <p className="text-lg font-bold">—</p>
            </div>
            <div className="flex-1 bg-white/10 rounded-xl p-3 text-center">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <Music size={14} />
                <span className="text-xs font-medium">Songs</span>
              </div>
              <p className="text-lg font-bold">—</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sharing Items */}
      <div className="px-4 py-5 space-y-3">
        {sharingItems.map(item => (
          <div
            key={item.id}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
          >
            <div className="p-4 flex items-start gap-4">
              <div className={`w-14 h-14 rounded-2xl ${item.bgColor} flex items-center justify-center ${item.textColor} flex-shrink-0`}>
                {item.icon}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-800 text-sm font-[Fredoka]">{item.title}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                {item.link ? (
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-flex items-center gap-1.5 mt-2.5 px-3 py-1.5 rounded-full text-xs font-semibold ${item.bgColor} ${item.textColor} hover:opacity-80 transition-opacity`}
                  >
                    <ExternalLink size={12} />
                    {item.linkLabel}
                  </a>
                ) : (
                  <div className="mt-2.5 px-3 py-1.5 rounded-full text-xs font-medium bg-gray-50 text-gray-400 inline-block">
                    Coming soon — link will be added by the team
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

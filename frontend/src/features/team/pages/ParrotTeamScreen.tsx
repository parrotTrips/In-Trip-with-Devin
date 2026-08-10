import { Loader2, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getMyTeam, type TeamMember } from '../../trip/services/trip-api';

function whatsappUrl(phone: string) {
  const digits = phone.replace(/\D/g, '');
  return `https://wa.me/${digits}`;
}

function MemberCard({ member }: { member: TeamMember }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex gap-4">
      {member.photo_url ? (
        <img
          src={member.photo_url}
          alt={member.name}
          className="w-16 h-16 rounded-full object-cover shrink-0 border border-gray-100"
        />
      ) : (
        <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center shrink-0 border border-emerald-100">
          <span className="text-2xl font-bold text-emerald-600">
            {member.name.charAt(0).toUpperCase()}
          </span>
        </div>
      )}

      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-semibold text-gray-800">{member.name}</h3>
        {member.function && (
          <p className="text-xs text-emerald-600 font-medium mt-0.5">{member.function}</p>
        )}
        {member.bio && (
          <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{member.bio}</p>
        )}
        {member.phone && (
          <a
            href={whatsappUrl(member.phone)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 bg-[#25D366] hover:bg-[#1ebe5d] text-white text-xs font-semibold rounded-full transition-colors"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5" aria-hidden="true">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
            </svg>
            WhatsApp
          </a>
        )}
      </div>
    </div>
  );
}

export default function ParrotTeamScreen() {
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyTeam()
      .then(r => setTeam(r.team))
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load team'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingBottom: 'calc(80px + env(safe-area-inset-bottom))' }}>
      <header className="bg-white border-b border-gray-100 px-4 pt-10 pb-4">
        <h1 className="text-xl font-bold text-gray-900 font-[Fredoka]">Parrot Team</h1>
        <p className="text-sm text-gray-500 mt-0.5">Your crew on this trip</p>
      </header>

      <div className="px-4 py-4 space-y-3">
        {loading && (
          <div className="flex justify-center py-12">
            <Loader2 className="animate-spin text-emerald-600" size={28} />
          </div>
        )}

        {error && (
          <div className="bg-red-50 rounded-2xl p-4 text-center">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {!loading && !error && team.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
              <Users size={28} className="text-gray-300" />
            </div>
            <p className="text-sm font-medium text-gray-500">No team members yet</p>
          </div>
        )}

        {team.map(member => (
          <MemberCard key={member.id} member={member} />
        ))}
      </div>
    </div>
  );
}

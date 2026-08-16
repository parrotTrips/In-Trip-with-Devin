import { ExternalLink, Loader2, Phone, ChevronDown, ChevronUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import posthog from 'posthog-js';
import {
  getMyTeam,
  getMyEmergencyContacts,
  getMyFaq,
  getMyAppFeedback,
  updateMyAppFeedback,
  type TeamMember,
  type EmergencyContact,
  type FaqItem,
} from '../../trip/services/trip-api';
import AppHeader from '../../../shared/components/AppHeader';

// ── CollapsibleSection (same pattern as ProfileScreen) ─────────────────────────

function CollapsibleSection({ title, emoji, children }: { title: string; emoji: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) posthog.capture('secao_informacao_aberta', { secao: title });
  };
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center text-lg">
            {emoji}
          </div>
          <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
        </div>
        {open ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
      </button>
      {open && <div className="px-4 pb-4 border-t border-gray-50">{children}</div>}
    </div>
  );
}

// ── Parrot Team ────────────────────────────────────────────────────────────────

function MemberCard({ member }: { member: TeamMember }) {
  return (
    <div className="flex gap-4 py-3 border-b border-gray-50 last:border-0">
      {member.photo_url ? (
        <img src={member.photo_url} alt={member.name} className="w-14 h-14 rounded-full object-cover shrink-0 border border-gray-100" />
      ) : (
        <div className="w-14 h-14 rounded-full bg-emerald-50 flex items-center justify-center shrink-0 border border-emerald-100">
          <span className="text-xl font-bold text-emerald-600">{member.name.charAt(0).toUpperCase()}</span>
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-gray-800">{member.name}</p>
        {member.function && <p className="text-xs text-emerald-600 font-medium mt-0.5">{member.function}</p>}
        {member.bio && <p className="text-xs text-gray-500 mt-1 leading-relaxed">{member.bio}</p>}
        {member.phone && (
          <a href={`https://wa.me/${member.phone.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 bg-[#25D366] text-white text-xs font-semibold rounded-full">
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" /></svg>
            {member.phone}
          </a>
        )}
      </div>
    </div>
  );
}

// ── Emergency Contacts ─────────────────────────────────────────────────────────

function EmergencyRow({ contact }: { contact: EmergencyContact }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
      <div>
        <p className="text-sm font-semibold text-gray-800">{contact.name}</p>
        {contact.role && <p className="text-xs text-gray-400">{contact.role}</p>}
      </div>
      {contact.phone && (
        <a href={`tel:${contact.phone}`} className="flex items-center gap-1.5 bg-red-50 text-red-600 text-xs font-semibold px-3 py-1.5 rounded-full whitespace-nowrap">
          <Phone size={12} />{contact.phone}
        </a>
      )}
    </div>
  );
}

// ── FAQ ────────────────────────────────────────────────────────────────────────

function FaqRow({ item }: { item: FaqItem }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-gray-50 last:border-0">
      <button onClick={() => setOpen(o => !o)} className="w-full flex items-center justify-between py-3 text-left gap-3">
        <p className="text-sm font-semibold text-gray-800">{item.question}</p>
        {open ? <ChevronUp size={15} className="text-gray-400 shrink-0" /> : <ChevronDown size={15} className="text-gray-400 shrink-0" />}
      </button>
      {open && <p className="text-sm text-gray-600 leading-relaxed pb-3">{item.answer}</p>}
    </div>
  );
}

// ── Empty ──────────────────────────────────────────────────────────────────────

function Empty({ label }: { label: string }) {
  return <p className="text-sm text-gray-400 py-4 text-center">{label}</p>;
}

// ── Main screen ────────────────────────────────────────────────────────────────

export default function InformationScreen() {
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [emergency, setEmergency] = useState<EmergencyContact[]>([]);
  const [faq, setFaq] = useState<FaqItem[]>([]);
  const [appFeedback, setAppFeedback] = useState('');
  const [feedbackSaving, setFeedbackSaving] = useState(false);
  const [feedbackSaved, setFeedbackSaved] = useState(false);
  const [feedbackError, setFeedbackError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getMyTeam().then(r => setTeam(r.team)),
      getMyEmergencyContacts().then(r => setEmergency(r.emergency_contacts)),
      getMyFaq().then(r => setFaq(r.faq)),
      getMyAppFeedback().then(r => setAppFeedback(r.feedback ?? '')),
    ])
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleFeedbackSave() {
    setFeedbackSaving(true);
    setFeedbackSaved(false);
    setFeedbackError(false);
    try {
      const response = await updateMyAppFeedback(appFeedback);
      setAppFeedback(response.feedback);
      setFeedbackSaved(true);
      posthog.capture('app_feedback_saved');
    } catch {
      setFeedbackError(true);
    } finally {
      setFeedbackSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-gray-50" style={{ paddingBottom: 'calc(100px + env(safe-area-inset-bottom))' }}>
      <AppHeader title="Information" />
      <div className="pt-14" />

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="animate-spin text-emerald-600" size={28} />
        </div>
      ) : (
        <div className="px-4 py-5 space-y-3">

          <CollapsibleSection title="Parrot Team" emoji="👥">
            {team.length === 0
              ? <Empty label="No team members yet" />
              : team.map(m => <MemberCard key={m.id} member={m} />)}
          </CollapsibleSection>

          <CollapsibleSection title="Emergency Contacts" emoji="🆘">
            {emergency.length === 0
              ? <Empty label="No emergency contacts yet" />
              : emergency.map(c => <EmergencyRow key={c.id} contact={c} />)}
          </CollapsibleSection>

          <Link
            to="/recommendations"
            onClick={() => posthog.capture('secao_informacao_aberta', { secao: 'Local Recommendations' })}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center text-lg">
                📍
              </div>
              <h3 className="text-sm font-semibold text-gray-800">Local Recommendations</h3>
            </div>
            <ExternalLink size={18} className="text-gray-400" />
          </Link>

          <CollapsibleSection title="FAQ" emoji="❓">
            {faq.length === 0
              ? <Empty label="No FAQ yet" />
              : faq.map(item => <FaqRow key={item.id} item={item} />)}
          </CollapsibleSection>

          <CollapsibleSection title="Feedback" emoji="💬">
            <div className="pt-3 space-y-3">
              <p className="text-sm text-gray-600 leading-relaxed">
                Conte para a gente o que funcionou bem no aplicativo e o que podemos melhorar nesta viagem.
              </p>
              <label className="block">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">App Feedback</span>
                <textarea
                  value={appFeedback}
                  onChange={event => {
                    setAppFeedback(event.target.value);
                    setFeedbackSaved(false);
                    setFeedbackError(false);
                  }}
                  maxLength={5000}
                  rows={5}
                  className="mt-2 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-emerald-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-100"
                  placeholder="Share your feedback about the app..."
                />
              </label>
              <button
                type="button"
                onClick={handleFeedbackSave}
                disabled={feedbackSaving}
                className="flex items-center justify-center gap-2 w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white rounded-xl font-medium text-sm transition-colors"
              >
                {feedbackSaving ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Saving...
                  </>
                ) : 'Save Feedback'}
              </button>
              {feedbackSaved && <p className="text-xs font-medium text-emerald-600">Feedback saved</p>}
              {feedbackError && <p className="text-xs font-medium text-red-500">Could not save feedback. Try again.</p>}
            </div>
          </CollapsibleSection>

        </div>
      )}
    </div>
  );
}

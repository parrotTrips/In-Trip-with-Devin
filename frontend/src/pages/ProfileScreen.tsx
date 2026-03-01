import { ArrowLeft, Plane, User, FileText, Smartphone, Users, ChevronDown, ChevronUp, Save, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { useState, useEffect } from 'react';
import { getProfile, updateProfile, getTripTravelers, type ProfileData, type TravelerInfo } from '../services/api';

const TRIP_ID = 'ross26';

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  emoji: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function CollapsibleSection({ title, emoji, children, defaultOpen = false }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center text-lg">
            {emoji}
          </div>
          <div className="text-left">
            <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
          </div>
        </div>
        {open ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
      </button>
      {open && <div className="px-4 pb-4 border-t border-gray-50">{children}</div>}
    </div>
  );
}

function InputField({ label, value, onChange, type = 'text', placeholder, disabled = false }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-500">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-gray-50 disabled:text-gray-400"
      />
    </div>
  );
}

function SelectField({ label, value, onChange, options }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-500">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all bg-white"
      >
        <option value="">Select...</option>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function TextAreaField({ label, value, onChange, placeholder }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-500">{label}</label>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all resize-none"
      />
    </div>
  );
}

export default function ProfileScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [travelers, setTravelers] = useState<TravelerInfo[]>([]);

  // Form state - all fields
  const [form, setForm] = useState<Record<string, string>>({
    preferred_name: '',
    email: '',
    dob: '',
    gender: '',
    transfer_platform: '',
    package_option: '',
    num_people: '',
    usd_amount: '',
    proof_of_transfer: '',
    dietary_restrictions_yn: '',
    dietary_restrictions_desc: '',
    seasickness_yn: '',
    first_name_passport: '',
    last_name_passport: '',
    passport_country: '',
    passport_number: '',
    passport_issue_date: '',
    passport_expiration_date: '',
    plus_one_yn: '',
    plus_one_name: '',
    plus_one_email: '',
    intl_flights_help_yn: '',
    intl_flights_help_details: '',
    travel_insurance_help_yn: '',
    unforgettable_trip_details: '',
    receive_addon_updates: '',
    esim_qr_image: '',
    roommate_user_id: '',
    arrival_date: '',
    arrival_time: '',
    arrival_flight: '',
    departure_date: '',
    departure_time: '',
    departure_flight: '',
    service_agreement_url: '',
  });

  const setField = (key: string, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  useEffect(() => {
    if (!user) return;
    const load = async () => {
      try {
        const [profileRes, travelersRes] = await Promise.all([
          getProfile(user.userId),
          getTripTravelers(TRIP_ID),
        ]);
        setTravelers(travelersRes.travelers);

        if (profileRes.profile) {
          const p = profileRes.profile;
          const newForm: Record<string, string> = {};
          for (const [key, val] of Object.entries(p)) {
            newForm[key] = val !== null && val !== undefined ? String(val) : '';
          }
          setForm(prev => ({ ...prev, ...newForm }));
        }
        // Pre-fill phone if not set
        if (!form.preferred_name && profileRes.name) {
          setForm(prev => ({ ...prev, preferred_name: profileRes.name || '' }));
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    try {
      const data: Partial<ProfileData> = {};
      for (const [key, val] of Object.entries(form)) {
        if (val !== '') {
          if (key === 'num_people') {
            (data as Record<string, unknown>)[key] = parseInt(val) || null;
          } else if (key === 'usd_amount') {
            (data as Record<string, unknown>)[key] = parseFloat(val) || null;
          } else if (key === 'roommate_user_id') {
            (data as Record<string, unknown>)[key] = parseInt(val) || null;
          } else {
            (data as Record<string, unknown>)[key] = val;
          }
        }
      }
      await updateProfile(user.userId, data);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Failed to save profile:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="animate-spin text-emerald-600" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-gray-50 pb-24">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
        <div className="flex items-center h-14 px-4 max-w-lg mx-auto">
          <button
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft size={22} className="text-gray-700" />
          </button>
          <h1 className="flex-1 text-center text-base font-semibold text-gray-800 font-[Fredoka] pr-8">
            My Profile
          </h1>
        </div>
      </header>

      <div className="pt-14">
        {/* Profile Header */}
        <div className="bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 px-5 py-6 text-white">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
              <User size={32} />
            </div>
            <div>
              <h2 className="text-xl font-bold font-[Fredoka]">
                {form.preferred_name || user?.name || 'Traveler'}
              </h2>
              <p className="text-emerald-100 text-sm">{user?.phone}</p>
              <p className="text-emerald-200 text-xs mt-1">Bernardo Brazil Trip 2026</p>
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 py-5 space-y-3">

        {/* ── Section 1: Products & Payment ── */}
        <CollapsibleSection title="Products & Payment" icon={<FileText size={18} />} emoji="🛒" defaultOpen={false}>
          <div className="pt-3 space-y-3">
            <InputField label="Package Option" value={form.package_option} onChange={v => setField('package_option', v)} placeholder="e.g. Full Package" />
            <div className="grid grid-cols-2 gap-3">
              <InputField label="# People" value={form.num_people} onChange={v => setField('num_people', v)} type="number" placeholder="1" />
              <InputField label="USD Amount" value={form.usd_amount} onChange={v => setField('usd_amount', v)} type="number" placeholder="0.00" />
            </div>
            <InputField label="Transfer Platform" value={form.transfer_platform} onChange={v => setField('transfer_platform', v)} placeholder="e.g. Wise, PayPal" />
            <InputField label="Proof of Transfer (URL)" value={form.proof_of_transfer} onChange={v => setField('proof_of_transfer', v)} placeholder="Link to receipt/screenshot" />
          </div>
        </CollapsibleSection>

        {/* ── Section 2: Service Agreement ── */}
        <CollapsibleSection title="Service Agreement" icon={<FileText size={18} />} emoji="📄" defaultOpen={false}>
          <div className="pt-3 space-y-3">
            <InputField label="Service Agreement URL" value={form.service_agreement_url} onChange={v => setField('service_agreement_url', v)} placeholder="Link to signed agreement" />
            {form.service_agreement_url && (
              <a
                href={form.service_agreement_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-emerald-600 hover:text-emerald-700 font-medium"
              >
                <FileText size={16} />
                View Service Agreement
              </a>
            )}
            {!form.service_agreement_url && (
              <p className="text-xs text-gray-400">No service agreement uploaded yet. The Parrot Trips team will share the link with you.</p>
            )}
          </div>
        </CollapsibleSection>

        {/* ── Section 3: eSIM QR Code ── */}
        <CollapsibleSection title="eSIM" icon={<Smartphone size={18} />} emoji="📱" defaultOpen={false}>
          <div className="pt-3 space-y-3">
            <InputField label="eSIM QR Code Image URL" value={form.esim_qr_image} onChange={v => setField('esim_qr_image', v)} placeholder="Paste image URL here" />
            {form.esim_qr_image && (
              <div className="bg-gray-50 rounded-xl p-4 flex justify-center">
                <img
                  src={form.esim_qr_image}
                  alt="eSIM QR Code"
                  className="max-w-[200px] max-h-[200px] rounded-lg"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              </div>
            )}
            {!form.esim_qr_image && (
              <div className="bg-gray-50 rounded-xl p-6 text-center">
                <Smartphone className="mx-auto text-gray-300 mb-2" size={32} />
                <p className="text-xs text-gray-400">Your eSIM QR code will appear here once provided by the Parrot Trips team.</p>
              </div>
            )}
          </div>
        </CollapsibleSection>

        {/* ── Section 4: Roommates ── */}
        <CollapsibleSection title="Roommate" icon={<Users size={18} />} emoji="🛏️" defaultOpen={false}>
          <div className="pt-3 space-y-3">
            <SelectField
              label="Select your roommate"
              value={form.roommate_user_id}
              onChange={v => setField('roommate_user_id', v)}
              options={travelers
                .filter(t => t.id !== user?.userId)
                .map(t => ({ value: String(t.id), label: t.name || t.phone }))}
            />
            {form.roommate_user_id && (
              <div className="bg-emerald-50 rounded-xl p-3 flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                  <Users size={18} className="text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {travelers.find(t => String(t.id) === form.roommate_user_id)?.name || 'Selected'}
                  </p>
                  <p className="text-xs text-gray-500">Your roommate for this trip</p>
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>

        {/* ── Section 5: Flights ── */}
        <CollapsibleSection title="Flight Information" icon={<Plane size={18} />} emoji="✈️" defaultOpen={false}>
          <div className="pt-3 space-y-4">
            <div>
              <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-2">Arrival</p>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <InputField label="Date" value={form.arrival_date} onChange={v => setField('arrival_date', v)} type="date" />
                  <InputField label="Time" value={form.arrival_time} onChange={v => setField('arrival_time', v)} type="time" />
                </div>
                <InputField label="Flight Number" value={form.arrival_flight} onChange={v => setField('arrival_flight', v)} placeholder="e.g. AA 900" />
              </div>
            </div>
            <div className="border-t border-gray-100 pt-4">
              <p className="text-xs font-semibold text-red-500 uppercase tracking-wide mb-2">Departure</p>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <InputField label="Date" value={form.departure_date} onChange={v => setField('departure_date', v)} type="date" />
                  <InputField label="Time" value={form.departure_time} onChange={v => setField('departure_time', v)} type="time" />
                </div>
                <InputField label="Flight Number" value={form.departure_flight} onChange={v => setField('departure_flight', v)} placeholder="e.g. AA 901" />
              </div>
            </div>
          </div>
        </CollapsibleSection>

        {/* ── Section 6: Registration Info ── */}
        <CollapsibleSection title="Registration Details" icon={<User size={18} />} emoji="📋" defaultOpen={false}>
          <div className="pt-3 space-y-3">
            <InputField label="Preferred Name" value={form.preferred_name} onChange={v => setField('preferred_name', v)} placeholder="How you'd like to be called" />
            <InputField label="Email" value={form.email} onChange={v => setField('email', v)} type="email" placeholder="your@email.com" />
            <div className="grid grid-cols-2 gap-3">
              <InputField label="Date of Birth" value={form.dob} onChange={v => setField('dob', v)} type="date" />
              <SelectField label="Gender" value={form.gender} onChange={v => setField('gender', v)} options={[
                { value: 'male', label: 'Male' },
                { value: 'female', label: 'Female' },
                { value: 'non-binary', label: 'Non-binary' },
                { value: 'prefer-not-to-say', label: 'Prefer not to say' },
              ]} />
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Passport Information</p>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <InputField label="First Name (as in passport)" value={form.first_name_passport} onChange={v => setField('first_name_passport', v)} />
                  <InputField label="Last Name (as in passport)" value={form.last_name_passport} onChange={v => setField('last_name_passport', v)} />
                </div>
                <InputField label="Passport Issuing Country" value={form.passport_country} onChange={v => setField('passport_country', v)} placeholder="e.g. United States" />
                <InputField label="Passport Number" value={form.passport_number} onChange={v => setField('passport_number', v)} />
                <div className="grid grid-cols-2 gap-3">
                  <InputField label="Issue Date" value={form.passport_issue_date} onChange={v => setField('passport_issue_date', v)} type="date" />
                  <InputField label="Expiration Date" value={form.passport_expiration_date} onChange={v => setField('passport_expiration_date', v)} type="date" />
                </div>
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Health & Dietary</p>
              <div className="space-y-3">
                <SelectField label="Dietary Restrictions?" value={form.dietary_restrictions_yn} onChange={v => setField('dietary_restrictions_yn', v)} options={[
                  { value: 'yes', label: 'Yes' },
                  { value: 'no', label: 'No' },
                ]} />
                {form.dietary_restrictions_yn === 'yes' && (
                  <TextAreaField label="Describe your dietary restrictions" value={form.dietary_restrictions_desc} onChange={v => setField('dietary_restrictions_desc', v)} placeholder="e.g. Vegetarian, gluten-free..." />
                )}
                <SelectField label="Prone to Seasickness?" value={form.seasickness_yn} onChange={v => setField('seasickness_yn', v)} options={[
                  { value: 'yes', label: 'Yes' },
                  { value: 'no', label: 'No' },
                ]} />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Plus One</p>
              <div className="space-y-3">
                <SelectField label="Bringing a Plus One?" value={form.plus_one_yn} onChange={v => setField('plus_one_yn', v)} options={[
                  { value: 'yes', label: 'Yes' },
                  { value: 'no', label: 'No' },
                ]} />
                {form.plus_one_yn === 'yes' && (
                  <>
                    <InputField label="Plus One Name" value={form.plus_one_name} onChange={v => setField('plus_one_name', v)} />
                    <InputField label="Plus One Email" value={form.plus_one_email} onChange={v => setField('plus_one_email', v)} type="email" />
                  </>
                )}
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Additional</p>
              <div className="space-y-3">
                <SelectField label="Need help with international flights?" value={form.intl_flights_help_yn} onChange={v => setField('intl_flights_help_yn', v)} options={[
                  { value: 'yes', label: 'Yes' },
                  { value: 'no', label: 'No' },
                ]} />
                {form.intl_flights_help_yn === 'yes' && (
                  <TextAreaField label="Flight help details" value={form.intl_flights_help_details} onChange={v => setField('intl_flights_help_details', v)} placeholder="Tell us what you need..." />
                )}
                <SelectField label="Need help with travel insurance?" value={form.travel_insurance_help_yn} onChange={v => setField('travel_insurance_help_yn', v)} options={[
                  { value: 'yes', label: 'Yes' },
                  { value: 'no', label: 'No' },
                ]} />
                <TextAreaField label="What would make this trip unforgettable?" value={form.unforgettable_trip_details} onChange={v => setField('unforgettable_trip_details', v)} placeholder="Share your ideas..." />
                <SelectField label="Receive updates about add-ons?" value={form.receive_addon_updates} onChange={v => setField('receive_addon_updates', v)} options={[
                  { value: 'yes', label: 'Yes' },
                  { value: 'no', label: 'No' },
                ]} />
              </div>
            </div>
          </div>
        </CollapsibleSection>
      </div>

      {/* Save button - fixed at bottom */}
      <div className="fixed bottom-16 left-0 right-0 px-4 pb-4 z-40">
        <div className="max-w-lg mx-auto">
          <button
            onClick={handleSave}
            disabled={saving}
            className={`w-full py-3.5 rounded-2xl font-semibold text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
              saved
                ? 'bg-emerald-500 text-white'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white'
            }`}
          >
            {saving ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Saving...
              </>
            ) : saved ? (
              <>
                <Save size={18} />
                Saved!
              </>
            ) : (
              <>
                <Save size={18} />
                Save Profile
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

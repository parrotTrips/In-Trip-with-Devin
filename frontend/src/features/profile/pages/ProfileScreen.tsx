import { User, FileText, ChevronDown, ChevronUp, Save, Loader2, ShoppingCart, ExternalLink, LogOut, QrCode, Camera } from 'lucide-react';
import { useEffect, useId, useRef, useState } from 'react';
import AppHeader from '../../../shared/components/AppHeader';
import { QRCodeSVG } from 'qrcode.react';
import { useAuth } from '../../../app/providers/auth-context';
import { useTripContext } from '../../../app/providers/trip-context';
import { useAvatar } from '../../../app/providers/avatar-context';
import { getProfile, updateProfile, type ProfileData } from '../services/profile-api';
import { getMyQrCode, type TravelerQrCode } from '../../trip/services/trip-api';

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
  const fieldId = useId();

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="text-xs font-medium text-gray-500">{label}</label>
      <input
        id={fieldId}
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

function ReadOnlyField({ label, value, placeholder }: {
  label: string;
  value: string;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-500">{label}</label>
      <div className="w-full px-3 py-2 text-sm border border-gray-100 rounded-xl bg-gray-50 text-gray-600">
        {value || <span className="text-gray-300">{placeholder || 'Not set'}</span>}
      </div>
    </div>
  );
}

function SelectField({ label, value, onChange, options }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  const fieldId = useId();

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="text-xs font-medium text-gray-500">{label}</label>
      <select
        id={fieldId}
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
  const fieldId = useId();

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="text-xs font-medium text-gray-500">{label}</label>
      <textarea
        id={fieldId}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all resize-none"
      />
    </div>
  );
}

const DOB_MONTHS = [
  { value: '01', label: 'January' },
  { value: '02', label: 'February' },
  { value: '03', label: 'March' },
  { value: '04', label: 'April' },
  { value: '05', label: 'May' },
  { value: '06', label: 'June' },
  { value: '07', label: 'July' },
  { value: '08', label: 'August' },
  { value: '09', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
];

function DateSelectField({ label, value, onChange }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 1929 }, (_, i) => currentYear - i);

  const parts = value ? value.split('-') : ['', '', ''];
  const selectedYear = parts[0] ?? '';
  const selectedMonth = parts[1] ?? '';
  const selectedDay = parts[2] ?? '';

  const daysInMonth = selectedYear && selectedMonth
    ? new Date(parseInt(selectedYear), parseInt(selectedMonth), 0).getDate()
    : 31;
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  const handleChange = (year: string, month: string, day: string) => {
    if (!year || !month || !day) { onChange(''); return; }
    // Clamp day if the new month/year has fewer days (e.g. switching from Jan 31 to Feb)
    const maxDays = new Date(parseInt(year), parseInt(month), 0).getDate();
    const clampedDay = Math.min(parseInt(day), maxDays);
    onChange(`${year}-${month}-${String(clampedDay).padStart(2, '0')}`);
  };

  const selectClass = "px-2 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all bg-white";

  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-gray-500">{label}</label>
      <div className="grid grid-cols-3 gap-2">
        <select
          aria-label="Day"
          value={selectedDay}
          onChange={e => handleChange(selectedYear, selectedMonth, e.target.value)}
          className={selectClass}
        >
          <option value="">Day</option>
          {days.map(d => (
            <option key={d} value={String(d).padStart(2, '0')}>{d}</option>
          ))}
        </select>
        <select
          aria-label="Month"
          value={selectedMonth}
          onChange={e => handleChange(selectedYear, e.target.value, selectedDay)}
          className={selectClass}
        >
          <option value="">Month</option>
          {DOB_MONTHS.map(m => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
        <select
          aria-label="Year"
          value={selectedYear}
          onChange={e => handleChange(e.target.value, selectedMonth, selectedDay)}
          className={selectClass}
        >
          <option value="">Year</option>
          {years.map(y => (
            <option key={y} value={String(y)}>{y}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const { setAvatarUrl } = useAvatar();
  const { tripInfo } = useTripContext();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const [qrCode, setQrCode] = useState<TravelerQrCode | null>(null);

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
    avatar_url: '',
  });

  const avatarInputRef = useRef<HTMLInputElement>(null);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const url = reader.result as string;
      setField('avatar_url', url);
      setAvatarUrl(url);
    };
    reader.readAsDataURL(file);
  };

  const setField = (key: string, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  useEffect(() => {
    if (!user) return;

    const load = async () => {
      try {
        const [profileRes, qrRes] = await Promise.allSettled([
          getProfile(user.userId),
          getMyQrCode(),
        ]);
        if (qrRes.status === 'fulfilled') setQrCode(qrRes.value);
        const profileRes2 = profileRes.status === 'fulfilled' ? profileRes.value : null;
        if (!profileRes2) { setLoading(false); return; }

        if (profileRes2.profile) {
          const p = profileRes2.profile;
          const newForm: Record<string, string> = {};
          for (const [key, val] of Object.entries(p)) {
            newForm[key] = val !== null && val !== undefined ? String(val) : '';
          }
          if (p.avatar_url) setAvatarUrl(p.avatar_url);
          setForm(prev => {
            const nextForm = { ...prev, ...newForm };
            if (!prev.preferred_name && profileRes2.name) {
              nextForm.preferred_name = profileRes2.name;
            }
            return nextForm;
          });
        } else if (profileRes2.name) {
          setForm(prev => (
            prev.preferred_name ? prev : { ...prev, preferred_name: profileRes2.name ?? '' }
          ));
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [user]);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    setSaveError(false);
    try {
      const data: Partial<ProfileData> = {};
      for (const [key, val] of Object.entries(form)) {
        if (val !== '') {
          if (key === 'num_people') {
            (data as Record<string, unknown>)[key] = parseInt(val) || null;
          } else if (key === 'usd_amount') {
            (data as Record<string, unknown>)[key] = parseFloat(val) || null;
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
      setSaveError(true);
      setTimeout(() => setSaveError(false), 4000);
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
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-gray-50" style={{ paddingBottom: 'calc(100px + env(safe-area-inset-bottom))' }}>
      <AppHeader title="My Profile" />

      <div className="pt-14">
        {/* Profile Header */}
        <div className="bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 px-5 py-6 text-white">
          <div className="flex items-center gap-4">
            <button
              onClick={() => avatarInputRef.current?.click()}
              className="relative shrink-0 group"
              aria-label="Change profile photo"
            >
              {form.avatar_url ? (
                <img
                  src={form.avatar_url}
                  alt="Profile"
                  className="w-16 h-16 rounded-full object-cover border-2 border-white/30"
                />
              ) : (
                <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center border-2 border-white/30">
                  <User size={32} />
                </div>
              )}
              <div className="absolute inset-0 rounded-full bg-black/30 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                <Camera size={18} className="text-white" />
              </div>
            </button>
            <input
              ref={avatarInputRef}
              type="file"
              accept="image/*"
              capture="user"
              className="hidden"
              onChange={handleAvatarChange}
            />
            <div>
              <h2 className="text-xl font-bold font-[Fredoka]">
                {form.preferred_name || user?.name || 'Traveler'}
              </h2>
              <p className="text-emerald-100 text-sm">{user?.phone}</p>
              {tripInfo && <p className="text-emerald-200 text-xs mt-1">{tripInfo.title}</p>}
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 py-5 space-y-3">

        {/* ── Section 1: My QR Code ── */}
        <CollapsibleSection title="My QR Code" icon={<QrCode size={18} />} emoji="📱" defaultOpen={false}>
          <div className="pt-3">
            {qrCode ? (
              <div className="flex items-center gap-4">
                <div className="shrink-0 rounded-xl border border-gray-100 bg-white p-2">
                  <QRCodeSVG value={qrCode.qr_payload} size={140} level="M" aria-label="Traveler check-in QR code" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-800">{form.preferred_name || user?.name || 'Traveler'}</p>
                  {tripInfo && <p className="text-sm text-emerald-700 mt-0.5">{tripInfo.title}</p>}
                  <p className="mt-2 text-xs text-gray-500 leading-5">Present this QR code to staff for check-in at activities.</p>
                </div>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-xl p-6 text-center">
                <QrCode className="mx-auto text-gray-300 mb-2" size={32} />
                <p className="text-sm font-medium text-gray-500">QR Code not available</p>
                <p className="text-xs text-gray-400 mt-1">Available once your trip is confirmed.</p>
              </div>
            )}
          </div>
        </CollapsibleSection>

        {/* ── Section 2: Registration Details ── */}
        <CollapsibleSection title="Registration Details" icon={<User size={18} />} emoji="📋" defaultOpen={false}>
          <div className="pt-3 space-y-3">
            <InputField label="Preferred Name" value={form.preferred_name} onChange={v => setField('preferred_name', v)} placeholder="How you'd like to be called" />
            <InputField label="Email" value={form.email} onChange={v => setField('email', v)} type="email" placeholder="your@email.com" />
            <div className="grid grid-cols-2 gap-3">
              <DateSelectField label="Date of Birth" value={form.dob} onChange={v => setField('dob', v)} />
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
              </div>
            </div>
          </div>
        </CollapsibleSection>

        {/* ── Section 2: Packages (non-editable basic package + Add-ons) ── */}
        <CollapsibleSection title="Packages" icon={<ShoppingCart size={18} />} emoji="🛒" defaultOpen={false}>
          <div className="pt-3 space-y-4">
            <div>
              <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-2">Your Package</p>
              <div className="bg-emerald-50 rounded-xl p-4 space-y-2">
                <ReadOnlyField label="Package Name" value={form.package_option} placeholder="Will be set by Parrot Trips team" />
                <ReadOnlyField label="Room Type" value={form.transfer_platform} placeholder="Will be set by Parrot Trips team" />
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Additional Activities Purchased</p>
              <div className="bg-gray-50 rounded-xl p-4">
                <ReadOnlyField label="Add-on Activities" value={form.proof_of_transfer} placeholder="No additional activities purchased yet" />
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Package Changes</p>
              <div className="bg-gray-50 rounded-xl p-4">
                <a
                  href="https://package-transfer-116789457910.southamerica-east1.run.app"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium text-sm transition-colors"
                >
                  Transfer or cancel your package
                  <ExternalLink size={14} />
                </a>
              </div>
            </div>
          </div>
        </CollapsibleSection>

        {/* ── Section 3: Service Agreement (per-trip, read-only) ── */}
        <CollapsibleSection title="Service Agreement" icon={<FileText size={18} />} emoji="📄" defaultOpen={false}>
          <div className="pt-3 space-y-3">
            {tripInfo?.service_agreement_url ? (
              <div className="space-y-3">
                <div className="bg-emerald-50 rounded-xl p-4 flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                    <FileText size={18} className="text-emerald-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">Service Agreement</p>
                    <p className="text-xs text-gray-500">Document provided by Parrot Trips</p>
                  </div>
                </div>
                <a
                  href={tripInfo.service_agreement_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium text-sm transition-colors"
                >
                  <FileText size={16} />
                  View Service Agreement
                  <ExternalLink size={14} />
                </a>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-xl p-6 text-center">
                <FileText className="mx-auto text-gray-300 mb-2" size={32} />
                <p className="text-sm font-medium text-gray-500">Not available yet</p>
                <p className="text-xs text-gray-400 mt-1">Your Service Agreement will be shared by the Parrot Trips team.</p>
              </div>
            )}
          </div>
        </CollapsibleSection>
      </div>

      {/* Save and Sign Out buttons */}
      <div className="px-4 pt-4">
        <div className="space-y-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className={`w-full py-3.5 rounded-2xl font-semibold text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
              saveError
                ? 'bg-red-500 text-white'
                : saved
                ? 'bg-emerald-500 text-white'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white'
            }`}
          >
            {saving ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Saving...
              </>
            ) : saveError ? (
              <>
                <Save size={18} />
                Error saving — try again
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

          <button
            onClick={logout}
            className="w-full py-3 rounded-2xl font-semibold text-sm flex items-center justify-center gap-2 text-red-500 bg-red-50 hover:bg-red-100 transition-colors"
          >
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

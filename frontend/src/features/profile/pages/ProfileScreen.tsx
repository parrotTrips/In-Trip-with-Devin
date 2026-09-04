import { User, FileText, ChevronDown, ChevronUp, Save, Loader2, ShoppingCart, ExternalLink, LogOut, QrCode, Camera, Info } from 'lucide-react';
import { useEffect, useId, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
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
  sectionId?: string;
}

function CollapsibleSection({ title, emoji, children, defaultOpen = false, sectionId }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!defaultOpen) return;

    setOpen(true);
    if (sectionId) {
      window.setTimeout(() => {
        sectionRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
      }, 0);
    }
  }, [defaultOpen, sectionId]);

  return (
    <div id={sectionId} ref={sectionRef} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden scroll-mt-16">
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

function FieldError({ id, error }: { id: string; error?: string }) {
  if (!error) return null;
  return <p id={id} className="text-xs font-medium text-red-600">{error}</p>;
}

function RequiredMark() {
  return <span className="text-red-500" aria-hidden="true">*</span>;
}

function InfoCallout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 rounded-xl bg-emerald-50 px-3 py-2 text-xs leading-5 text-emerald-900">
      <Info size={14} className="mt-0.5 shrink-0 text-emerald-700" aria-hidden="true" />
      <p>{children}</p>
    </div>
  );
}

function InputField({ label, value, onChange, type = 'text', placeholder, disabled = false, required = false, error }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
}) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="flex items-center gap-1 text-xs font-medium text-gray-500">
        {label}
        {required && <RequiredMark />}
      </label>
      <input
        id={fieldId}
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={`w-full min-w-0 px-3 py-2 text-sm border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-gray-50 disabled:text-gray-400 ${
          error ? 'border-red-300 bg-red-50/40' : 'border-gray-200'
        }`}
      />
      <FieldError id={errorId} error={error} />
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

function SelectField({ label, value, onChange, options, required = false, error, disabled = false }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  required?: boolean;
  error?: string;
  disabled?: boolean;
}) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="flex items-center gap-1 text-xs font-medium text-gray-500">
        {label}
        {required && <RequiredMark />}
      </label>
      <select
        id={fieldId}
        value={value}
        onChange={e => onChange(e.target.value)}
        required={required}
        disabled={disabled}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={`w-full min-w-0 px-3 py-2 text-sm border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all disabled:bg-gray-50 disabled:text-gray-400 ${
          error ? 'border-red-300 bg-red-50/40' : 'border-gray-200 bg-white'
        }`}
      >
        <option value="">Select...</option>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <FieldError id={errorId} error={error} />
    </div>
  );
}

function TextAreaField({ label, value, onChange, placeholder, required = false, error }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  error?: string;
}) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="flex items-center gap-1 text-xs font-medium text-gray-500">
        {label}
        {required && <RequiredMark />}
      </label>
      <textarea
        id={fieldId}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
        required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={`w-full min-w-0 px-3 py-2 text-sm border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all resize-none ${
          error ? 'border-red-300 bg-red-50/40' : 'border-gray-200'
        }`}
      />
      <FieldError id={errorId} error={error} />
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

const VISA_STATUS_OPTIONS = [
  { value: 'Yes, I already have a visa / I can enter Brazil without a visa', label: 'Yes, I already have a visa / I can enter Brazil without a visa' },
  { value: "Not yet, I already started my visa process but don't have one yet", label: "Not yet, I already started my visa process but don't have one yet" },
  { value: "No, I am required to have a visa but didn't start the application so far.", label: "No, I am required to have a visa but didn't start the application so far." },
  { value: 'I am not sure and I need orientation about it', label: 'I am not sure and I need orientation about it' },
];

const CHECKED_BAGS_OPTIONS = [
  { value: 'No checked bags, I travel light', label: 'No checked bags, I travel light' },
  { value: '1 checked bag is all I need', label: '1 checked bag is all I need' },
  { value: 'More than 1 checked bag and I will take care of the extra costs.', label: 'More than 1 checked bag and I will take care of the extra costs.' },
];

const TRAVEL_INSURANCE_STATUS_OPTIONS = [
  { value: 'Already hired one', label: 'Already hired one' },
  { value: 'I will use one provided by my credit card (or something like that)', label: 'I will use one provided by my credit card (or something like that)' },
  { value: "I don't have one yet, but I will since is mandatory", label: "I don't have one yet, but I will since is mandatory" },
];

const ROOMMATE_STATUS_OPTIONS = [
  { value: 'Yes', label: 'Yes' },
  { value: 'No, please match me with someone.', label: 'No, please match me with someone.' },
  { value: 'I am staying in an individual room', label: 'I am staying in an individual room' },
];

const ROOM_CONFIGURATION_OPTIONS = [
  { value: 'One double bed (for two people)', label: 'One double bed (for two people)' },
  { value: 'Two twin beds (one single bed each)', label: 'Two twin beds (one single bed each)' },
];

const EARLY_CHECK_IN_OPTIONS = [
  { value: "I’ll arrive after the check-in time.", label: "I’ll arrive after the check-in time." },
  { value: "I’ll arrive early but prefer not to pay extra; I’m happy with your best effort.", label: "I’ll arrive early but prefer not to pay extra; I’m happy with your best effort." },
  { value: "I’ll arrive early and would rather pay the full daily rate to guarantee early check-in.", label: "I’ll arrive early and would rather pay the full daily rate to guarantee early check-in." },
];

const PROFILE_SECTION_IDS = new Set([
  'qr-code',
  'registration',
  'pre-departure',
  'packages',
  'service-agreement',
]);

const PRE_DEPARTURE_REMOVED_FIELDS = new Set([
  'trip_mood',
  'social_topic',
  'always_up_for',
  'roommate_email',
]);

const PRE_DEPARTURE_REQUIRED_LABELS: Record<string, string> = {
  visa_status: 'Visa Status',
  arrival_date: 'Arrival Date',
  arrival_flight: 'Arrival Airport and Flight',
  checked_bags: 'Checked Bags',
  extended_stay_help: 'Early arrival or longer stay',
  extended_stay_help_details: 'How can we help?',
  early_check_in_preference: 'Early Check-in Preference',
  departure_date: 'Departure Date',
  departure_flight: 'Departure Airport and Flight',
  travel_insurance_status: 'Travel Insurance Status',
  travel_insurance_brazil_medical_coverage: 'Medical Coverage in Brazil',
  travel_insurance_provider: 'Insurance Provider',
  travel_insurance_policy_number: 'Policy Number',
  roommate_status: 'Roommate Status',
  roommate_user_id: 'Requested Roommate',
  room_configuration: 'Room Configuration',
  roommate_gender_preference: 'Roommate Gender Preference',
  emergency_contact: 'Emergency Contact',
};

function getLinkedProfileSection(search: string) {
  const section = new URLSearchParams(search).get('section');
  return section && PROFILE_SECTION_IDS.has(section) ? section : null;
}

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
  const location = useLocation();
  const { user, logout } = useAuth();
  const { setAvatarUrl } = useAvatar();
  const { tripInfo, travelers } = useTripContext();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
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
    visa_status: '',
    arrival_date: '',
    arrival_time: '',
    arrival_flight: '',
    departure_date: '',
    departure_time: '',
    departure_flight: '',
    checked_bags: '',
    travel_insurance_status: '',
    travel_insurance_brazil_medical_coverage: '',
    travel_insurance_provider: '',
    travel_insurance_policy_number: '',
    travel_insurance_notes: '',
    roommate_status: '',
    roommate_user_id: '',
    roommate_email: '',
    room_configuration: '',
    roommate_gender_preference: '',
    extended_stay_help: '',
    extended_stay_help_details: '',
    early_check_in_preference: '',
    emergency_contact: '',
    instagram_handle: '',
    trip_mood: '',
    social_topic: '',
    always_up_for: '',
    home_address: '',
    final_considerations: '',
  });
  const linkedSection = getLinkedProfileSection(location.search);

  const avatarInputRef = useRef<HTMLInputElement>(null);
  const roommateOptions = travelers
    .filter(traveler => traveler.id !== user?.userId)
    .map(traveler => ({
      value: traveler.id,
      label: traveler.name || traveler.phone || 'Traveler',
    }));

  const requireField = (errors: Record<string, string>, key: string) => {
    if (!form[key]?.trim()) {
      errors[key] = `${PRE_DEPARTURE_REQUIRED_LABELS[key]} is required`;
    }
  };

  const validatePreDeparture = () => {
    const errors: Record<string, string> = {};
    [
      'visa_status',
      'arrival_date',
      'arrival_flight',
      'checked_bags',
      'extended_stay_help',
      'early_check_in_preference',
      'departure_date',
      'departure_flight',
      'travel_insurance_status',
      'travel_insurance_brazil_medical_coverage',
      'travel_insurance_provider',
      'travel_insurance_policy_number',
      'roommate_status',
      'room_configuration',
      'emergency_contact',
    ].forEach(key => requireField(errors, key));

    if (form.extended_stay_help === 'Yes, please') {
      requireField(errors, 'extended_stay_help_details');
    }
    if (form.roommate_status === 'Yes') {
      requireField(errors, 'roommate_user_id');
    }
    if (form.roommate_status === 'No, please match me with someone.') {
      requireField(errors, 'roommate_gender_preference');
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

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
    setValidationErrors(prev => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setSaved(false);
  };

  const setRoommateStatus = (value: string) => {
    setForm(prev => ({
      ...prev,
      roommate_status: value,
      roommate_user_id: value === 'Yes' ? prev.roommate_user_id : '',
      roommate_email: '',
      roommate_gender_preference: value === 'No, please match me with someone.' ? prev.roommate_gender_preference : '',
    }));
    setValidationErrors(prev => {
      const next = { ...prev };
      delete next.roommate_status;
      delete next.roommate_user_id;
      delete next.roommate_email;
      delete next.roommate_gender_preference;
      return next;
    });
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

  const handleSave = async ({ validate = false }: { validate?: boolean } = {}) => {
    if (!user) return;
    if (validate && !validatePreDeparture()) {
      setSaved(false);
      return;
    }
    setSaving(true);
    setSaveError(false);
    try {
      const data: Partial<ProfileData> = {};
      for (const [key, val] of Object.entries(form)) {
        if (PRE_DEPARTURE_REMOVED_FIELDS.has(key)) continue;
        if (key === 'roommate_user_id' && form.roommate_status !== 'Yes') continue;
        if (key === 'roommate_gender_preference' && form.roommate_status !== 'No, please match me with someone.') continue;
        if (key === 'extended_stay_help_details' && form.extended_stay_help !== 'Yes, please') continue;
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
        <CollapsibleSection title="My QR Code" icon={<QrCode size={18} />} emoji="📱" sectionId="qr-code" defaultOpen={linkedSection === 'qr-code'}>
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
        <CollapsibleSection title="Registration Details" icon={<User size={18} />} emoji="📋" sectionId="registration" defaultOpen={linkedSection === 'registration'}>
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

            <div className="border-t border-gray-100 pt-3">
              <button
                onClick={() => handleSave()}
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
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        </CollapsibleSection>

        {/* ── Section 3: Pre Departure Information ── */}
        <CollapsibleSection title="Pre Departure Information" icon={<FileText size={18} />} emoji="🧳" sectionId="pre-departure" defaultOpen={linkedSection === 'pre-departure'}>
          <div className="pt-3 space-y-3">
            <SelectField label="Visa Status" value={form.visa_status} onChange={v => setField('visa_status', v)} options={VISA_STATUS_OPTIONS} required error={validationErrors.visa_status} />

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Arrival</p>
              <div className="space-y-3">
                <div data-testid="arrival-date-time-grid" className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <InputField label="Arrival Date" value={form.arrival_date} onChange={v => setField('arrival_date', v)} type="date" required error={validationErrors.arrival_date} />
                  <InputField label="Arrival Time" value={form.arrival_time} onChange={v => setField('arrival_time', v)} type="time" />
                </div>
                <InputField label="Arrival Airport and Flight" value={form.arrival_flight} onChange={v => setField('arrival_flight', v)} placeholder="e.g. GRU, AA 1234" required error={validationErrors.arrival_flight} />
                <SelectField label="Checked Bags" value={form.checked_bags} onChange={v => setField('checked_bags', v)} options={CHECKED_BAGS_OPTIONS} required error={validationErrors.checked_bags} />
                <SelectField label="Need help with early arrival or longer stay?" value={form.extended_stay_help} onChange={v => setField('extended_stay_help', v)} required error={validationErrors.extended_stay_help} options={[
                  { value: 'Yes, please', label: 'Yes, please' },
                  { value: 'No, thanks', label: 'No, thanks' },
                ]} />
                {form.extended_stay_help === 'Yes, please' && (
                  <TextAreaField label="How can we help?" value={form.extended_stay_help_details} onChange={v => setField('extended_stay_help_details', v)} required error={validationErrors.extended_stay_help_details} />
                )}
                <InfoCallout>
                  Hotels usually have a 2 PM check-in time. While we always strive to have your room ready upon arrival for the trek, it’s not guaranteed. While bag drop and common areas are okay, early check-in may involve a fee
                </InfoCallout>
                <SelectField label="Early Check-in Preference" value={form.early_check_in_preference} onChange={v => setField('early_check_in_preference', v)} options={EARLY_CHECK_IN_OPTIONS} required error={validationErrors.early_check_in_preference} />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Departure</p>
              <div className="space-y-3">
                <div data-testid="departure-date-time-grid" className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <InputField label="Departure Date" value={form.departure_date} onChange={v => setField('departure_date', v)} type="date" required error={validationErrors.departure_date} />
                  <InputField label="Departure Time" value={form.departure_time} onChange={v => setField('departure_time', v)} type="time" />
                </div>
                <InputField label="Departure Airport and Flight" value={form.departure_flight} onChange={v => setField('departure_flight', v)} placeholder="e.g. GIG, LA 4567" required error={validationErrors.departure_flight} />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Travel Insurance</p>
              <div className="space-y-3">
                <SelectField label="Travel Insurance Status" value={form.travel_insurance_status} onChange={v => setField('travel_insurance_status', v)} options={TRAVEL_INSURANCE_STATUS_OPTIONS} required error={validationErrors.travel_insurance_status} />
                <SelectField label="Medical Coverage in Brazil" value={form.travel_insurance_brazil_medical_coverage} onChange={v => setField('travel_insurance_brazil_medical_coverage', v)} required error={validationErrors.travel_insurance_brazil_medical_coverage} options={[
                  { value: 'Yes', label: 'Yes' },
                  { value: 'No', label: 'No' },
                  { value: 'Not sure, but I will find out', label: 'Not sure, but I will find out' },
                ]} />
                <InputField label="Insurance Provider" value={form.travel_insurance_provider} onChange={v => setField('travel_insurance_provider', v)} required error={validationErrors.travel_insurance_provider} />
                <InputField label="Policy Number" value={form.travel_insurance_policy_number} onChange={v => setField('travel_insurance_policy_number', v)} required error={validationErrors.travel_insurance_policy_number} />
                <TextAreaField label="Travel Insurance Notes" value={form.travel_insurance_notes} onChange={v => setField('travel_insurance_notes', v)} />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Room Preferences</p>
              <div className="space-y-3">
                <SelectField label="Do you know who you will share the room with?" value={form.roommate_status} onChange={setRoommateStatus} options={ROOMMATE_STATUS_OPTIONS} required error={validationErrors.roommate_status} />
                {form.roommate_status === 'Yes' && (
                  <SelectField
                    label="Requested Roommate"
                    value={form.roommate_user_id}
                    onChange={v => setField('roommate_user_id', v)}
                    options={roommateOptions}
                    required
                    error={validationErrors.roommate_user_id}
                    disabled={roommateOptions.length === 0}
                  />
                )}
                <SelectField label="Room Configuration" value={form.room_configuration} onChange={v => setField('room_configuration', v)} options={ROOM_CONFIGURATION_OPTIONS} required error={validationErrors.room_configuration} />
                {form.roommate_status === 'No, please match me with someone.' && (
                  <SelectField label="Roommate Gender Preference" value={form.roommate_gender_preference} onChange={v => setField('roommate_gender_preference', v)} required error={validationErrors.roommate_gender_preference} options={[
                    { value: 'Female', label: 'Female' },
                    { value: 'Male', label: 'Male' },
                    { value: 'No preference', label: 'No preference' },
                  ]} />
                )}
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Contact & Social</p>
              <div className="space-y-3">
                <InputField label="Emergency Contact" value={form.emergency_contact} onChange={v => setField('emergency_contact', v)} placeholder="Name and phone number" required error={validationErrors.emergency_contact} />
                <InfoCallout>
                  We will be posting moments of the trip in our Instagram account. If want to be tagged and followed by us, put your @ here :)
                </InfoCallout>
                <InputField label="Instagram Handle" value={form.instagram_handle} onChange={v => setField('instagram_handle', v)} placeholder="@yourhandle" />
                <InfoCallout>
                  Some hotels ask for this info on the check in and if you want to speed it up, please inform here. Totally optional :)
                </InfoCallout>
                <InputField label="Home Address" value={form.home_address} onChange={v => setField('home_address', v)} />
                <TextAreaField label="Final Considerations" value={form.final_considerations} onChange={v => setField('final_considerations', v)} />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3">
              <button
                onClick={() => handleSave({ validate: true })}
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
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        </CollapsibleSection>

        {/* ── Section 2: Packages (non-editable basic package + Add-ons) ── */}
        <CollapsibleSection title="Packages" icon={<ShoppingCart size={18} />} emoji="🛒" sectionId="packages" defaultOpen={linkedSection === 'packages'}>
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
              <div className="bg-gray-50 rounded-xl p-4 space-y-2">
                <a
                  href="https://www.wetravel.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl font-medium text-sm transition-colors"
                >
                  Manage My Payments
                  <ExternalLink size={14} />
                </a>
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
        <CollapsibleSection title="Service Agreement" icon={<FileText size={18} />} emoji="📄" sectionId="service-agreement" defaultOpen={linkedSection === 'service-agreement'}>
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

      {/* Sign Out button */}
      <div className="px-4 pt-4">
        <div className="space-y-2">
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

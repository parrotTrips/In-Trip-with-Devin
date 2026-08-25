import { useState } from 'react';
import ParrotLogoIcon from '../../../shared/components/ParrotLogoIcon';
import { requestOTP, verifyOTP } from '../services/auth-api';
import { useAuth } from '../../../app/providers/auth-context';

const countryCallingCodeRegions = {
  '+1': 'US', '+7': 'RU', '+20': 'EG', '+27': 'ZA', '+30': 'GR',
  '+31': 'NL', '+32': 'BE', '+33': 'FR', '+34': 'ES', '+36': 'HU',
  '+39': 'IT', '+40': 'RO', '+41': 'CH', '+43': 'AT', '+44': 'GB',
  '+45': 'DK', '+46': 'SE', '+47': 'NO', '+48': 'PL', '+49': 'DE',
  '+51': 'PE', '+52': 'MX', '+53': 'CU', '+54': 'AR', '+55': 'BR',
  '+56': 'CL', '+57': 'CO', '+58': 'VE', '+60': 'MY', '+61': 'AU',
  '+62': 'ID', '+63': 'PH', '+64': 'NZ', '+65': 'SG', '+66': 'TH',
  '+81': 'JP', '+82': 'KR', '+84': 'VN', '+86': 'CN', '+90': 'TR',
  '+91': 'IN', '+92': 'PK', '+93': 'AF', '+94': 'LK', '+95': 'MM',
  '+98': 'IR', '+211': 'SS', '+212': 'MA', '+213': 'DZ', '+216': 'TN',
  '+218': 'LY', '+220': 'GM', '+221': 'SN', '+222': 'MR', '+223': 'ML',
  '+224': 'GN', '+225': 'CI', '+226': 'BF', '+227': 'NE', '+228': 'TG',
  '+229': 'BJ', '+230': 'MU', '+231': 'LR', '+232': 'SL', '+233': 'GH',
  '+234': 'NG', '+235': 'TD', '+236': 'CF', '+237': 'CM', '+238': 'CV',
  '+239': 'ST', '+240': 'GQ', '+241': 'GA', '+242': 'CG', '+243': 'CD',
  '+244': 'AO', '+245': 'GW', '+246': 'IO', '+247': 'AC', '+248': 'SC',
  '+249': 'SD', '+250': 'RW', '+251': 'ET', '+252': 'SO', '+253': 'DJ',
  '+254': 'KE', '+255': 'TZ', '+256': 'UG', '+257': 'BI', '+258': 'MZ',
  '+260': 'ZM', '+261': 'MG', '+262': 'RE', '+263': 'ZW', '+264': 'NA',
  '+265': 'MW', '+266': 'LS', '+267': 'BW', '+268': 'SZ', '+269': 'KM',
  '+290': 'SH', '+291': 'ER', '+297': 'AW', '+298': 'FO', '+299': 'GL',
  '+350': 'GI', '+351': 'PT', '+352': 'LU', '+353': 'IE', '+354': 'IS',
  '+355': 'AL', '+356': 'MT', '+357': 'CY', '+358': 'FI', '+359': 'BG',
  '+370': 'LT', '+371': 'LV', '+372': 'EE', '+373': 'MD', '+374': 'AM',
  '+375': 'BY', '+376': 'AD', '+377': 'MC', '+378': 'SM', '+380': 'UA',
  '+381': 'RS', '+382': 'ME', '+383': 'XK', '+385': 'HR', '+386': 'SI',
  '+387': 'BA', '+389': 'MK', '+420': 'CZ', '+421': 'SK', '+423': 'LI',
  '+500': 'FK', '+501': 'BZ', '+502': 'GT', '+503': 'SV', '+504': 'HN',
  '+505': 'NI', '+506': 'CR', '+507': 'PA', '+508': 'PM', '+509': 'HT',
  '+590': 'GP', '+591': 'BO', '+592': 'GY', '+593': 'EC', '+594': 'GF',
  '+595': 'PY', '+596': 'MQ', '+597': 'SR', '+598': 'UY', '+599': 'CW',
  '+670': 'TL', '+672': 'NF', '+673': 'BN', '+674': 'NR', '+675': 'PG',
  '+676': 'TO', '+677': 'SB', '+678': 'VU', '+679': 'FJ', '+680': 'PW',
  '+681': 'WF', '+682': 'CK', '+683': 'NU', '+685': 'WS', '+686': 'KI',
  '+687': 'NC', '+688': 'TV', '+689': 'PF', '+690': 'TK', '+691': 'FM',
  '+692': 'MH', '+850': 'KP', '+852': 'HK', '+853': 'MO', '+855': 'KH',
  '+856': 'LA', '+880': 'BD', '+886': 'TW', '+960': 'MV', '+961': 'LB',
  '+962': 'JO', '+963': 'SY', '+964': 'IQ', '+965': 'KW', '+966': 'SA',
  '+967': 'YE', '+968': 'OM', '+970': 'PS', '+971': 'AE', '+972': 'IL',
  '+973': 'BH', '+974': 'QA', '+975': 'BT', '+976': 'MN', '+977': 'NP',
  '+992': 'TJ', '+993': 'TM', '+994': 'AZ', '+995': 'GE', '+996': 'KG',
  '+998': 'UZ',
} as const;

const countryCallingCodes = Object.keys(countryCallingCodeRegions) as Array<keyof typeof countryCallingCodeRegions>;

function flagForRegion(region: string) {
  return region
    .toUpperCase()
    .replace(/./g, char => String.fromCodePoint(127397 + char.charCodeAt(0)));
}

export default function LoginScreen() {
  const { login } = useAuth();
  const [step, setStep] = useState<'phone' | 'code'>('phone');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [debugCode, setDebugCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countryCode, setCountryCode] = useState('+1');

  const fullPhone = `${countryCode}${phone}`;

  const handleSendCode = async () => {
    if (!phone || phone.length < 8) return;
    setLoading(true);
    setError('');
    try {
      const response = await requestOTP(fullPhone);
      setDebugCode(response.debug_code ?? null);
      setStep('code');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (codeStr: string) => {
    setLoading(true);
    setError('');
    try {
      const result = await verifyOTP(fullPhone, codeStr);
      login(result.user_id, result.phone, result.name, result.access_token, result.role ?? 'traveler');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid code');
      setLoading(false);
    }
  };

  const handleCodeChange = (index: number, value: string) => {
    if (value.length > 1) return;
    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    if (value && index < 5) {
      document.getElementById(`code-${index + 1}`)?.focus();
    }

    if (value && index === 5 && newCode.every(c => c)) {
      handleVerifyCode(newCode.join(''));
    }
  };

  const handleCodeKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      const prev = document.getElementById(`code-${index - 1}`);
      prev?.focus();
      const newCode = [...code];
      newCode[index - 1] = '';
      setCode(newCode);
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const digits = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!digits) return;
    const newCode = [...code];
    digits.split('').forEach((d, i) => { newCode[i] = d; });
    setCode(newCode);
    // Focus last filled input
    const lastIndex = Math.min(digits.length - 1, 5);
    document.getElementById(`code-${lastIndex}`)?.focus();
    if (digits.length === 6) {
      handleVerifyCode(digits);
    }
  };

  return (
    <div className="min-h-dvh bg-gradient-to-b from-emerald-700 via-emerald-600 to-teal-700 flex flex-col">
      {/* Decorative top elements */}
      <div className="absolute top-0 left-0 right-0 h-96 overflow-hidden pointer-events-none">
        <div className="absolute top-10 -left-10 w-40 h-40 bg-emerald-500/30 rounded-full blur-3xl" />
        <div className="absolute top-20 right-0 w-32 h-32 bg-teal-400/30 rounded-full blur-3xl" />
        <div className="absolute top-40 left-1/3 w-24 h-24 bg-yellow-400/20 rounded-full blur-2xl" />
      </div>

      <div className="relative flex-1 flex flex-col items-center justify-center px-4 py-8 safe-top safe-bottom">
        {/* Brand icon */}
        <div className="text-center mb-6">
          <ParrotLogoIcon size={64} className="mx-auto mb-3" color="#ffffff" />
          <h1 className="text-2xl font-bold text-white font-[Fredoka]">Parrot Trips</h1>
          <p className="text-emerald-100 text-xs mt-1">Your Brazilian Adventure Awaits!</p>
        </div>

        {/* Login Card */}
        <div className="w-full max-w-sm bg-white rounded-3xl shadow-2xl p-5 relative overflow-hidden">
          {step === 'phone' ? (
            <>
              <h2 className="text-lg font-bold text-gray-800 font-[Fredoka] text-center mb-1">
                Welcome, Traveler!
              </h2>
              <p className="text-sm text-gray-500 text-center mb-6">
                Enter your phone number to receive a verification code via WhatsApp
              </p>

              <div className="flex gap-2 mb-4 w-full">
                <select
                  value={countryCode}
                  onChange={e => setCountryCode(e.target.value)}
                  className="w-24 flex-shrink-0 py-3 px-2 bg-gray-50 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 outline-none focus:ring-2 focus:ring-emerald-300"
                >
                  {countryCallingCodes.map(code => (
                    <option key={code} value={code}>
                      {flagForRegion(countryCallingCodeRegions[code])} {code}
                    </option>
                  ))}
                </select>
                <input
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
                  placeholder="Phone number"
                  className="flex-1 min-w-0 py-3 px-4 bg-gray-50 rounded-xl border border-gray-200 text-sm outline-none focus:ring-2 focus:ring-emerald-300"
                  maxLength={15}
                />
              </div>

              {error && (
                <p className="text-red-500 text-xs text-center mb-3">{error}</p>
              )}

              <button
                onClick={handleSendCode}
                disabled={loading || phone.length < 8}
                className="w-full py-3.5 bg-emerald-600 text-white rounded-xl font-semibold text-sm hover:bg-emerald-700 disabled:opacity-50 disabled:hover:bg-emerald-600 transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                    </svg>
                    Send WhatsApp Code
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              <h2 className="text-lg font-bold text-gray-800 font-[Fredoka] text-center mb-1">
                Verification Code
              </h2>
              <p className="text-sm text-gray-500 text-center mb-6">
                Enter the 6-digit code sent to<br />
                <span className="font-semibold text-gray-700">{countryCode} {phone}</span>
              </p>

              {debugCode && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2 text-center mb-4">
                  Test code: {debugCode}
                </p>
              )}

              <div className="flex gap-1.5 justify-center mb-6">
                {code.map((digit, i) => (
                  <input
                    key={i}
                    id={`code-${i}`}
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={1}
                    value={digit}
                    onChange={e => handleCodeChange(i, e.target.value)}
                    onKeyDown={e => handleCodeKeyDown(i, e)}
                    onPaste={handlePaste}
                    className="w-10 h-12 text-center text-xl font-bold bg-gray-50 rounded-xl border-2 border-gray-200 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all"
                  />
                ))}
              </div>

              {loading && (
                <div className="flex justify-center mb-4">
                  <div className="w-6 h-6 border-2 border-emerald-200 border-t-emerald-600 rounded-full animate-spin" />
                </div>
              )}

              {error && (
                <p className="text-red-500 text-xs text-center mb-3">{error}</p>
              )}

              <button
                onClick={() => {
                  setStep('phone');
                  setCode(['', '', '', '', '', '']);
                  setDebugCode(null);
                }}
                className="w-full text-sm text-gray-500 hover:text-emerald-600 transition-colors text-center"
              >
                ← Change phone number
              </button>

              <button
                className="w-full mt-3 text-sm text-emerald-600 font-medium hover:text-emerald-700 transition-colors text-center"
                onClick={async () => {
                  setLoading(true);
                  setError('');
                  try {
                    const response = await requestOTP(fullPhone);
                    setDebugCode(response.debug_code ?? null);
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'Failed to resend');
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                Resend code via WhatsApp
              </button>
            </>
          )}
        </div>

        {/* Footer */}
        <p className="text-emerald-200/60 text-xs mt-8 text-center">
          By continuing, you agree to our Terms of Service
        </p>
      </div>
    </div>
  );
}

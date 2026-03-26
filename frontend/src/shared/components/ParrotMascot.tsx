interface ParrotMascotProps {
  size?: number;
  className?: string;
  showSpeech?: boolean;
  speechText?: string;
}

export default function ParrotMascot({
  size = 48,
  className = '',
  showSpeech,
  speechText,
}: ParrotMascotProps) {
  return (
    <div className={`relative inline-flex items-center ${className}`}>
      {showSpeech && speechText && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-white rounded-xl px-3 py-1.5 shadow-lg border border-gray-100 whitespace-nowrap z-10">
          <p className="text-xs font-medium text-gray-700">{speechText}</p>
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-white border-r border-b border-gray-100 rotate-45" />
        </div>
      )}
      <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="50" cy="58" rx="22" ry="28" fill="#2EA043" />
        <ellipse cx="50" cy="62" rx="14" ry="18" fill="#86EFAC" />
        <circle cx="50" cy="32" r="18" fill="#0969DA" />
        <circle cx="43" cy="28" r="6" fill="white" />
        <circle cx="57" cy="28" r="6" fill="white" />
        <circle cx="44" cy="27" r="3" fill="#1a1a1a" />
        <circle cx="58" cy="27" r="3" fill="#1a1a1a" />
        <circle cx="45" cy="26" r="1" fill="white" />
        <circle cx="59" cy="26" r="1" fill="white" />
        <path d="M46 34 L50 42 L54 34 Z" fill="#F5C518" />
        <path d="M46 34 L50 37 L54 34 Z" fill="#F4845F" />
        <ellipse cx="28" cy="55" rx="10" ry="16" fill="#0969DA" transform="rotate(-15 28 55)" />
        <ellipse cx="72" cy="55" rx="10" ry="16" fill="#0969DA" transform="rotate(15 72 55)" />
        <ellipse cx="27" cy="58" rx="6" ry="10" fill="#E63946" transform="rotate(-15 27 58)" />
        <ellipse cx="73" cy="58" rx="6" ry="10" fill="#E63946" transform="rotate(15 73 58)" />
        <ellipse cx="42" cy="86" rx="6" ry="3" fill="#F5C518" />
        <ellipse cx="58" cy="86" rx="6" ry="3" fill="#F5C518" />
        <path d="M42 18 L44 10 L48 16 L50 8 L52 16 L56 10 L58 18" stroke="#E63946" strokeWidth="2" fill="#E63946" />
      </svg>
    </div>
  );
}

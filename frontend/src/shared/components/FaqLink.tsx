import { HelpCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import posthog from 'posthog-js';

// The trip FAQ lives on the Information screen; this opens it already expanded.
export const FAQ_PATH = '/information?section=faq';

export default function FaqLink({ from }: { from: string }) {
  return (
    <Link
      to={FAQ_PATH}
      onClick={() => posthog.capture('faq_aberto_da_jornada', { origem: from })}
      className="flex items-center justify-center gap-1.5 py-4 text-sm font-medium text-emerald-700 hover:text-emerald-800"
    >
      <HelpCircle size={16} />
      Questions? See the FAQ
    </Link>
  );
}

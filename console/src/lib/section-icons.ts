import {
  CalendarDays, ClipboardList, FileText, Folder, Heart, HelpCircle, ListChecks, MapPin,
  Megaphone, MessageSquare, Phone, Siren, UserCog, Users, type LucideIcon,
} from 'lucide-react';

const SECTION_ICONS: Record<string, LucideIcon> = {
  fases: ListChecks,
  roteiro: CalendarDays,
  recomendacoes: MapPin,
  faq: HelpCircle,
  politica_cancelamento: FileText,
  contatos_emergencia: Siren,
  viajantes: Users,
  staff: UserCog,
  contatos_operacionais: Phone,
  avisos: Megaphone,
  tarefas_staff: ClipboardList,
  'wrap-up': Heart,
  feedbacks: MessageSquare,
};

export function sectionIcon(key: string): LucideIcon {
  return SECTION_ICONS[key] ?? Folder;
}

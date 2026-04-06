import { ArrowLeft, Phone, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const contacts = [
  {
    category: 'Parrot Trips Team',
    items: [
      {
        name: 'Vitor Sanches',
        role: 'Trip Leader',
        phone: '+55 11 99766-6680',
        whatsapp: true,
      },
      {
        name: 'Parrot Trips Office',
        role: 'Operations',
        phone: '+55 11 99766-6680',
        whatsapp: true,
      },
    ],
  },
  {
    category: 'Emergency Services (Brazil)',
    items: [
      {
        name: 'Police (SAMU)',
        role: 'Emergency',
        phone: '190',
        whatsapp: false,
      },
      {
        name: 'Ambulance (SAMU)',
        role: 'Medical Emergency',
        phone: '192',
        whatsapp: false,
      },
      {
        name: 'Fire Department',
        role: 'Emergency',
        phone: '193',
        whatsapp: false,
      },
      {
        name: 'Tourist Police (Rio)',
        role: 'DEAT - Delegacia Especial de Apoio ao Turismo',
        phone: '+55 21 2332-2924',
        whatsapp: false,
      },
    ],
  },
  {
    category: 'Hospitals & Clinics',
    items: [
      {
        name: 'Hospital Copa Star',
        role: 'Copacabana — Private, English-speaking staff',
        phone: '+55 21 2545-3600',
        whatsapp: false,
      },
      {
        name: 'Hospital Samaritano',
        role: 'Botafogo — 24h Emergency',
        phone: '+55 21 2535-4000',
        whatsapp: false,
      },
    ],
  },
  {
    category: 'Embassies & Consulates (Rio)',
    items: [
      {
        name: 'US Consulate General',
        role: 'Av. Presidente Wilson, 147 - Centro',
        phone: '+55 21 3823-2000',
        whatsapp: false,
      },
      {
        name: 'British Consulate General',
        role: 'Praia do Flamengo, 284 - Flamengo',
        phone: '+55 21 2555-9600',
        whatsapp: false,
      },
    ],
  },
  {
    category: 'Hotels',
    items: [
      {
        name: 'Astoria Ipanema Hotel',
        role: 'Rio de Janeiro (Feb 27 - Mar 1)',
        phone: '+55 21 2523-0060',
        whatsapp: false,
      },
      {
        name: 'Recreio Da Praia Hotel',
        role: 'Ilha Grande (Mar 1 - Mar 5)',
        phone: '+55 24 3361-5169',
        whatsapp: false,
      },
    ],
  },
];

export default function EmergencyContacts() {
  const navigate = useNavigate();

  const handleCall = (phone: string) => {
    window.open(`tel:${phone.replace(/[\s()-]/g, '')}`, '_self');
  };

  const handleWhatsApp = (phone: string) => {
    const cleaned = phone.replace(/[\s()+-]/g, '');
    window.open(`https://wa.me/${cleaned}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-red-50 via-white to-orange-50 pb-20">
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
            Emergency Contacts
          </h1>
        </div>
      </header>

      <div className="pt-14">
        {/* Alert Banner */}
        <div className="bg-gradient-to-br from-red-600 via-red-500 to-orange-600 px-5 py-6 text-white">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center text-2xl">
              🆘
            </div>
            <div>
              <h2 className="text-xl font-bold font-[Fredoka]">Emergency Contacts</h2>
              <p className="text-red-100 text-sm">Important numbers for your trip</p>
            </div>
          </div>
        </div>

        {/* Tip */}
        <div className="mx-4 mt-4 bg-amber-50 border border-amber-200 rounded-2xl p-4">
          <p className="text-xs text-amber-800">
            <span className="font-semibold">Tip:</span> Save these contacts on your phone before the trip.
            In Brazil, dial <span className="font-bold">190</span> for police and <span className="font-bold">192</span> for ambulance.
          </p>
        </div>
      </div>

      {/* Contact Groups */}
      <div className="px-4 py-5 space-y-5">
        {contacts.map(group => (
          <div key={group.category}>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 px-1">
              {group.category}
            </h3>
            <div className="space-y-2">
              {group.items.map(contact => (
                <div
                  key={contact.name}
                  className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-800">{contact.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{contact.role}</p>
                      <p className="text-xs text-gray-400 mt-1 font-mono">{contact.phone}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-3">
                      {contact.whatsapp && (
                        <button
                          onClick={() => handleWhatsApp(contact.phone)}
                          className="p-2.5 rounded-xl bg-green-50 hover:bg-green-100 transition-colors"
                        >
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="#25D366">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                          </svg>
                        </button>
                      )}
                      <button
                        onClick={() => handleCall(contact.phone)}
                        className="p-2.5 rounded-xl bg-blue-50 hover:bg-blue-100 transition-colors"
                      >
                        <Phone size={18} className="text-blue-600" />
                      </button>
                      {!contact.whatsapp && contact.phone.startsWith('+') && (
                        <button
                          onClick={() => {
                            window.open(`https://www.google.com/maps/search/${encodeURIComponent(contact.role)}`, '_blank');
                          }}
                          className="p-2.5 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
                        >
                          <ExternalLink size={18} className="text-gray-500" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

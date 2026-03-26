import TopBar from '../components/TopBar';
import { Download, Eye, Folder } from 'lucide-react';

const documents = [
  {
    category: 'Trip Details',
    files: [
      { name: 'Complete Itinerary', type: 'PDF', size: '2.4 MB', icon: '📋' },
      { name: 'Hotel Confirmations', type: 'PDF', size: '1.1 MB', icon: '🏨' },
      { name: 'Flight Tickets', type: 'PDF', size: '890 KB', icon: '✈️' },
    ],
  },
  {
    category: 'Health & Safety',
    files: [
      { name: 'Vaccination Requirements', type: 'PDF', size: '450 KB', icon: '💉' },
      { name: 'Travel Insurance Policy', type: 'PDF', size: '3.2 MB', icon: '🛡️' },
      { name: 'Emergency Contacts', type: 'PDF', size: '120 KB', icon: '🆘' },
    ],
  },
  {
    category: 'Visa & Entry',
    files: [
      { name: 'Visa Application Guide', type: 'PDF', size: '680 KB', icon: '🛂' },
      { name: 'Required Documents Checklist', type: 'PDF', size: '350 KB', icon: '✅' },
    ],
  },
  {
    category: 'Practical Info',
    files: [
      { name: 'Packing List', type: 'PDF', size: '200 KB', icon: '🧳' },
      { name: 'Currency & Tips Guide', type: 'PDF', size: '310 KB', icon: '💰' },
      { name: 'Portuguese Phrasebook', type: 'PDF', size: '520 KB', icon: '🗣️' },
      { name: 'Restaurant Recommendations', type: 'PDF', size: '1.5 MB', icon: '🍽️' },
    ],
  },
];

export default function DocumentsScreen() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 via-white to-gray-50 pb-20">
      <TopBar title="Documents" />

      <div className="pt-14">
        {/* Header */}
        <div className="bg-gradient-to-br from-blue-600 via-blue-500 to-indigo-600 px-5 py-6 text-white">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
              <Folder size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold font-[Fredoka]">Trip Documents</h2>
              <p className="text-blue-200 text-sm">All your files in one place</p>
            </div>
          </div>
        </div>
      </div>

      {/* Documents */}
      <div className="px-4 py-5 space-y-5">
        {documents.map(category => (
          <div key={category.category}>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 px-1">
              {category.category}
            </h3>
            <div className="space-y-2">
              {category.files.map(file => (
                <div
                  key={file.name}
                  className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex items-center gap-3 hover:shadow-md transition-shadow"
                >
                  <div className="w-11 h-11 bg-blue-50 rounded-xl flex items-center justify-center text-lg flex-shrink-0">
                    {file.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{file.name}</p>
                    <p className="text-xs text-gray-400">{file.type} · {file.size}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button className="p-2 rounded-xl hover:bg-gray-100 transition-colors text-gray-400 hover:text-blue-500">
                      <Eye size={16} />
                    </button>
                    <button className="p-2 rounded-xl hover:bg-gray-100 transition-colors text-gray-400 hover:text-blue-500">
                      <Download size={16} />
                    </button>
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

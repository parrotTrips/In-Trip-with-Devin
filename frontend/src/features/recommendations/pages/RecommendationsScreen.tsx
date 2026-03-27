import { ArrowLeft, MapPin, Star, ExternalLink, Utensils, Wine, Coffee, ShoppingBag, Sparkles, Waves } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

type Category = 'all' | 'restaurants' | 'bars' | 'cafes' | 'wellness' | 'shopping' | 'beaches';

interface Recommendation {
  id: string;
  name: string;
  category: Category;
  neighborhood: string;
  location: 'rio' | 'ilha-grande';
  description: string;
  highlight?: string;
  priceRange?: string;
  rating?: number;
  mapUrl?: string;
  emoji: string;
}

const recommendations: Recommendation[] = [
  // ── Restaurants ──
  {
    id: 'r1',
    name: 'Babbo Osteria',
    category: 'restaurants',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Upscale Italian cuisine in a cozy setting. Great pasta and wine selection.',
    highlight: 'Near the hotel',
    priceRange: '$$$',
    rating: 4.7,
    mapUrl: 'https://maps.google.com/?q=Babbo+Osteria+Ipanema+Rio',
    emoji: '🍝',
  },
  {
    id: 'r2',
    name: 'Teva Bistro',
    category: 'restaurants',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Excellent vegan restaurant with creative plant-based dishes. Beautiful presentation.',
    highlight: 'Vegan-friendly',
    priceRange: '$$',
    rating: 4.8,
    mapUrl: 'https://maps.google.com/?q=Teva+Bistro+Ipanema+Rio',
    emoji: '🥗',
  },
  {
    id: 'r3',
    name: 'Zaza Bistro Tropical',
    category: 'restaurants',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Tropical-inspired fusion cuisine in a bohemian atmosphere. Famous for their creative cocktails and unique dishes.',
    priceRange: '$$$',
    rating: 4.6,
    mapUrl: 'https://maps.google.com/?q=Zaza+Bistro+Tropical+Ipanema+Rio',
    emoji: '🌴',
  },
  {
    id: 'r4',
    name: 'Pope Ipanema',
    category: 'restaurants',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Trendy restaurant with a modern Brazilian menu. Great for groups.',
    priceRange: '$$',
    rating: 4.5,
    mapUrl: 'https://maps.google.com/?q=Pope+Ipanema+Rio',
    emoji: '🍽️',
  },
  {
    id: 'r5',
    name: 'CT Boucherie',
    category: 'restaurants',
    neighborhood: 'Leblon',
    location: 'rio',
    description: 'Top-rated steakhouse by chef Claude Troisgros. Premium cuts with a French-Brazilian twist.',
    highlight: 'Must-try steakhouse',
    priceRange: '$$$$',
    rating: 4.8,
    mapUrl: 'https://maps.google.com/?q=CT+Boucherie+Leblon+Rio',
    emoji: '🥩',
  },
  {
    id: 'r6',
    name: 'Oro Restaurante',
    category: 'restaurants',
    neighborhood: 'Leblon',
    location: 'rio',
    description: 'Fine dining Brazilian cuisine. Michelin-recommended with an innovative tasting menu.',
    highlight: 'Fine dining',
    priceRange: '$$$$',
    rating: 4.9,
    mapUrl: 'https://maps.google.com/?q=Oro+Restaurante+Leblon+Rio',
    emoji: '✨',
  },
  {
    id: 'r7',
    name: 'Marius Degustare',
    category: 'restaurants',
    neighborhood: 'Leme',
    location: 'rio',
    description: 'Famous rodizio-style restaurant with premium meats and seafood buffet.',
    priceRange: '$$$',
    rating: 4.5,
    mapUrl: 'https://maps.google.com/?q=Marius+Degustare+Leme+Rio',
    emoji: '🦐',
  },
  {
    id: 'r8',
    name: 'Aprazivel',
    category: 'restaurants',
    neighborhood: 'Santa Teresa',
    location: 'rio',
    description: 'Stunning treehouse-style restaurant in Santa Teresa with panoramic views. Brazilian comfort food.',
    highlight: 'Amazing views',
    priceRange: '$$$',
    rating: 4.7,
    mapUrl: 'https://maps.google.com/?q=Aprazivel+Santa+Teresa+Rio',
    emoji: '🌿',
  },

  // ── Bars ──
  {
    id: 'b1',
    name: 'La Carioca En La Playa',
    category: 'bars',
    neighborhood: 'Leblon',
    location: 'rio',
    description: 'Beach bar where Cariocas end their week. Barefoot vibes, caipirinhas, and sunsets over the ocean.',
    highlight: 'Welcome Happy Hour venue',
    priceRange: '$$',
    rating: 4.5,
    mapUrl: 'https://maps.google.com/?q=La+Carioca+En+La+Playa+Leblon',
    emoji: '🏖️',
  },
  {
    id: 'b2',
    name: 'Bosque Bar',
    category: 'bars',
    neighborhood: 'Botafogo',
    location: 'rio',
    description: 'Live samba venue in a charming outdoor garden setting. Authentic samba experience with great energy.',
    highlight: 'Samba night venue',
    priceRange: '$$',
    rating: 4.6,
    mapUrl: 'https://maps.google.com/?q=Bosque+Bar+Botafogo+Rio',
    emoji: '🎵',
  },
  {
    id: 'b3',
    name: 'Pedra do Sal',
    category: 'bars',
    neighborhood: 'Centro / Saude',
    location: 'rio',
    description: 'The birthplace of samba! Open-air samba parties on Monday and Friday nights. A must-visit for authentic Rio culture.',
    highlight: 'Birthplace of samba',
    priceRange: '$',
    rating: 4.8,
    mapUrl: 'https://maps.google.com/?q=Pedra+do+Sal+Rio',
    emoji: '🥁',
  },
  {
    id: 'b4',
    name: 'Bar Astor',
    category: 'bars',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Classic Ipanema bar with great cocktails and people-watching. Popular with locals and visitors alike.',
    priceRange: '$$',
    rating: 4.4,
    mapUrl: 'https://maps.google.com/?q=Bar+Astor+Ipanema+Rio',
    emoji: '🍸',
  },
  {
    id: 'b5',
    name: 'Rio Scenarium',
    category: 'bars',
    neighborhood: 'Lapa',
    location: 'rio',
    description: 'Legendary multi-floor venue in Lapa filled with antiques and live music. Samba, forró, and more.',
    highlight: 'Iconic nightlife spot',
    priceRange: '$$',
    rating: 4.5,
    mapUrl: 'https://maps.google.com/?q=Rio+Scenarium+Lapa+Rio',
    emoji: '🎭',
  },

  // ── Cafes ──
  {
    id: 'c1',
    name: 'Zona Sul Supermarket',
    category: 'cafes',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Premium supermarket near the hotel. Great for stocking up on water, snacks, and local treats at better prices than hotel mini-bar.',
    highlight: 'Money-saving tip',
    priceRange: '$',
    mapUrl: 'https://maps.google.com/?q=Zona+Sul+Supermarket+Ipanema',
    emoji: '🛒',
  },
  {
    id: 'c2',
    name: 'Confeitaria Colombo',
    category: 'cafes',
    neighborhood: 'Centro',
    location: 'rio',
    description: 'Historic 1894 tea house with stunning Belle Epoque architecture. Famous pastries and afternoon tea.',
    highlight: 'Historic landmark',
    priceRange: '$$',
    rating: 4.7,
    mapUrl: 'https://maps.google.com/?q=Confeitaria+Colombo+Centro+Rio',
    emoji: '☕',
  },

  // ── Wellness ──
  {
    id: 'w1',
    name: 'Astoria Hotel Spa',
    category: 'wellness',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'In-hotel spa. Book at reception for massages and treatments. Convenient after a day at the beach.',
    highlight: 'In your hotel',
    priceRange: '$$',
    mapUrl: 'https://maps.google.com/?q=Astoria+Ipanema+Hotel',
    emoji: '💆',
  },
  {
    id: 'w2',
    name: 'Astoria Hotel Gym',
    category: 'wellness',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Open 24 hours. Well-equipped fitness center in the hotel.',
    highlight: 'Open 24h',
    priceRange: 'Free',
    emoji: '🏋️',
  },
  {
    id: 'w3',
    name: 'Rooftop (Astoria)',
    category: 'wellness',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Hotel rooftop with sunset views. Open Fri-Sun 1:00 PM - 9:00 PM. Perfect for relaxing after excursions.',
    highlight: 'Sunset views',
    priceRange: 'Free',
    emoji: '🌅',
  },

  // ── Shopping ──
  {
    id: 's1',
    name: 'Shopping Leblon',
    category: 'shopping',
    neighborhood: 'Leblon',
    location: 'rio',
    description: 'Upscale shopping mall with international and Brazilian brands. Also has a great food court.',
    priceRange: '$$$',
    mapUrl: 'https://maps.google.com/?q=Shopping+Leblon+Rio',
    emoji: '🛍️',
  },
  {
    id: 's2',
    name: 'Feira de Sao Cristovao',
    category: 'shopping',
    neighborhood: 'Sao Cristovao',
    location: 'rio',
    description: 'Massive Northeastern Brazilian market. Music, food, crafts, and authentic culture. Best on weekends.',
    highlight: 'Cultural experience',
    priceRange: '$',
    rating: 4.6,
    mapUrl: 'https://maps.google.com/?q=Feira+Sao+Cristovao+Rio',
    emoji: '🎪',
  },
  {
    id: 's3',
    name: 'Hippie Fair (Ipanema)',
    category: 'shopping',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Famous Sunday open-air market at Praca General Osorio. Handicrafts, art, jewelry, and souvenirs.',
    highlight: 'Sundays only',
    priceRange: '$-$$',
    rating: 4.5,
    mapUrl: 'https://maps.google.com/?q=Feira+Hippie+Ipanema+Rio',
    emoji: '🎨',
  },

  // ── Beaches ──
  {
    id: 'beach1',
    name: 'Ipanema Beach',
    category: 'beaches',
    neighborhood: 'Ipanema',
    location: 'rio',
    description: 'Iconic beach just 2 blocks from the hotel. Rent chairs and umbrellas on the sand. Try Mate Gelado, Biscoito Globo, and Queijo Coalho from beach vendors.',
    highlight: 'Steps from hotel',
    mapUrl: 'https://maps.google.com/?q=Ipanema+Beach+Rio',
    emoji: '🏖️',
  },
  {
    id: 'beach2',
    name: 'Copacabana Beach',
    category: 'beaches',
    neighborhood: 'Copacabana',
    location: 'rio',
    description: 'Walk along Ipanema to reach Copacabana. Visit the Copacabana Fort for great views. Open Tue-Sun 10am-7pm (entrance fee).',
    mapUrl: 'https://maps.google.com/?q=Copacabana+Beach+Rio',
    emoji: '🌊',
  },
  {
    id: 'beach3',
    name: 'Praia de Lopes Mendes',
    category: 'beaches',
    neighborhood: 'Ilha Grande',
    location: 'ilha-grande',
    description: 'Considered one of the most beautiful beaches in Brazil. Crystal clear water and pristine white sand.',
    highlight: 'Top beach in Brazil',
    mapUrl: 'https://maps.google.com/?q=Lopes+Mendes+Ilha+Grande',
    emoji: '🐚',
  },
  {
    id: 'beach4',
    name: 'Lagoa Azul',
    category: 'beaches',
    neighborhood: 'Ilha Grande',
    location: 'ilha-grande',
    description: 'Stunning blue lagoon with calm, crystal-clear water. Perfect for snorkeling and swimming.',
    highlight: 'Snorkeling paradise',
    mapUrl: 'https://maps.google.com/?q=Lagoa+Azul+Ilha+Grande',
    emoji: '🐠',
  },
];

const categories: { key: Category; label: string; icon: React.ReactNode }[] = [
  { key: 'all', label: 'All', icon: <Star size={14} /> },
  { key: 'restaurants', label: 'Food', icon: <Utensils size={14} /> },
  { key: 'bars', label: 'Bars', icon: <Wine size={14} /> },
  { key: 'cafes', label: 'Cafes', icon: <Coffee size={14} /> },
  { key: 'beaches', label: 'Beaches', icon: <Waves size={14} /> },
  { key: 'wellness', label: 'Wellness', icon: <Sparkles size={14} /> },
  { key: 'shopping', label: 'Shopping', icon: <ShoppingBag size={14} /> },
];

export default function RecommendationsScreen() {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState<Category>('all');
  const [activeLocation, setActiveLocation] = useState<'all' | 'rio' | 'ilha-grande'>('all');

  const filtered = recommendations.filter(r => {
    if (activeCategory !== 'all' && r.category !== activeCategory) return false;
    if (activeLocation !== 'all' && r.location !== activeLocation) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 via-white to-orange-50 pb-20">
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
            Local Recommendations
          </h1>
        </div>
      </header>

      <div className="pt-14">
        {/* Hero */}
        <div className="bg-gradient-to-br from-amber-600 via-orange-500 to-red-500 px-5 py-6 text-white">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center text-2xl">
              📍
            </div>
            <div>
              <h2 className="text-xl font-bold font-[Fredoka]">Local Recommendations</h2>
              <p className="text-amber-100 text-sm">Curated spots by the Parrot Trips team</p>
            </div>
          </div>
        </div>

        {/* Location Tabs */}
        <div className="px-4 pt-4 flex gap-2">
          {[
            { key: 'all' as const, label: 'All Locations' },
            { key: 'rio' as const, label: 'Rio de Janeiro' },
            { key: 'ilha-grande' as const, label: 'Ilha Grande' },
          ].map(loc => (
            <button
              key={loc.key}
              onClick={() => setActiveLocation(loc.key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                activeLocation === loc.key
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {loc.label}
            </button>
          ))}
        </div>

        {/* Category Filter */}
        <div className="px-4 pt-3 pb-2 overflow-x-auto">
          <div className="flex gap-2">
            {categories.map(cat => (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                  activeCategory === cat.key
                    ? 'bg-gray-800 text-white shadow-sm'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {cat.icon}
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results count */}
      <div className="px-5 py-2">
        <p className="text-xs text-gray-400">{filtered.length} recommendation{filtered.length !== 1 ? 's' : ''}</p>
      </div>

      {/* Recommendations List */}
      <div className="px-4 space-y-3 pb-4">
        {filtered.map(rec => (
          <div
            key={rec.id}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center text-xl flex-shrink-0">
                {rec.emoji}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-sm font-semibold text-gray-800">{rec.name}</h3>
                  {rec.highlight && (
                    <span className="text-[10px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
                      {rec.highlight}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <MapPin size={10} />
                    {rec.neighborhood}
                  </span>
                  {rec.priceRange && (
                    <span className="text-xs text-gray-400">{rec.priceRange}</span>
                  )}
                  {rec.rating && (
                    <span className="text-xs text-amber-500 flex items-center gap-0.5">
                      <Star size={10} fill="currentColor" />
                      {rec.rating}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-1.5 leading-relaxed">{rec.description}</p>
                {rec.mapUrl && (
                  <a
                    href={rec.mapUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-amber-600 hover:text-amber-700 font-medium mt-2"
                  >
                    <ExternalLink size={12} />
                    Open in Maps
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

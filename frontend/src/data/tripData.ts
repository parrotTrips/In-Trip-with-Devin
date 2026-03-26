export interface Traveler {
  id: string;
  name: string;
  avatar: string;
  currentPhaseId: string;
  phone?: string;
}

export interface ChecklistItem {
  id: string;
  text: string;
  completed: boolean;
}

export interface Comment {
  id: string;
  userId: string;
  userName: string;
  userAvatar: string;
  text: string;
  timestamp: string;
  isTeam?: boolean;
}

export interface Phase {
  id: string;
  type: 'pre-trip' | 'in-trip';
  title: string;
  subtitle?: string;
  icon: string;
  description: string;
  detailedDescription?: string;
  checklist?: ChecklistItem[];
  links?: { label: string; url: string }[];
  attachments?: { name: string; type: string }[];
  comments: Comment[];
  completed: boolean;
  locked: boolean;
  order: number;
}

export interface Activity {
  id: string;
  name: string;
  type: 'included' | 'optional' | 'suggested' | 'logistics';
  time: string;
  duration: string;
  description: string;
  practicalInfo: string;
  price?: string;
  images: string[];
  vibe?: string;
}

export interface TripDay extends Phase {
  activities: Activity[];
  albumPhotos: { id: string; url: string; userName: string; caption: string }[];
}

export const travelers: Traveler[] = [
  { id: '1', name: 'Bernardo', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
  { id: '2', name: 'Kristen', avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
  { id: '3', name: 'Jonathan', avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day2' },
  { id: '4', name: 'Daniel', avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
  { id: '5', name: 'Bailey', avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day2' },
  { id: '6', name: 'Terry', avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
  { id: '7', name: 'Isaiah', avatar: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day2' },
  { id: '8', name: 'Jasmin', avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
  { id: '9', name: 'Tyler', avatar: 'https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day2' },
  { id: '10', name: 'DeVar', avatar: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
  { id: '11', name: 'Dario', avatar: 'https://images.unsplash.com/photo-1504257432389-52343af06ae3?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day2' },
  { id: '12', name: 'Ivan', avatar: 'https://images.unsplash.com/photo-1463453091185-61582044d556?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
  { id: '13', name: 'Jacqueline', avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day2' },
  { id: '14', name: 'Abrahm', avatar: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=100&h=100&fit=crop&crop=face', currentPhaseId: 'day3' },
];

export const preTripPhases: Phase[] = [
  {
    id: 'visa',
    type: 'pre-trip',
    title: 'Visa',
    subtitle: 'Entry Requirements',
    icon: 'passport',
    description: 'Visa requirements for Brazil',
    detailedDescription: 'Brazil requires a valid visa or electronic travel authorization for entry depending on your nationality. US citizens need an eVisa which can be obtained online. Make sure your passport is valid for at least 6 months beyond your travel dates.\n\nProcessing times vary — apply early to avoid last-minute issues. Keep a printed copy of your visa approval as backup.',
    checklist: [
      { id: 'visa-1', text: 'Check if your nationality requires a visa for Brazil', completed: true },
      { id: 'visa-2', text: 'Ensure passport is valid for 6+ months beyond travel dates', completed: true },
      { id: 'visa-3', text: 'Apply for eVisa on the official Brazilian government portal', completed: true },
      { id: 'visa-4', text: 'Save/print visa approval confirmation', completed: true },
      { id: 'visa-5', text: 'Share visa approval with Parrot Trips team', completed: true },
    ],
    links: [
      { label: 'Brazil eVisa Portal', url: 'https://www.gov.br/mre/pt-br/assuntos/portal-consular/vistos/informacoes-sobre-vistos-para-estrangeiros-viajarem-ao-brasil' },
      { label: 'US Citizens Visa Info', url: 'https://www.gov.br/mre/en/subjects/consular-portal/visas' },
    ],
    completed: true,
    locked: false,
    order: 0,
    comments: [],
  },
  {
    id: 'vaccination',
    type: 'pre-trip',
    title: 'Vaccination',
    subtitle: 'Health Requirements',
    icon: 'syringe',
    description: 'Required vaccinations for travel to Brazil',
    detailedDescription: 'Yellow Fever vaccination is strongly recommended for travelers visiting Brazil, especially if you plan to visit areas outside major cities. Some countries require proof of Yellow Fever vaccination for re-entry after visiting Brazil.\n\nCOVID-19 vaccination is no longer required for entry but is recommended. Consult your doctor about other recommended vaccines such as Hepatitis A/B, Typhoid, and routine immunizations.\n\nBring your vaccination card or International Certificate of Vaccination (yellow card) with you.',
    checklist: [
      { id: 'vax-1', text: 'Check CDC/WHO recommendations for Brazil travel vaccines', completed: true },
      { id: 'vax-2', text: 'Get Yellow Fever vaccination (recommended)', completed: true },
      { id: 'vax-3', text: 'Ensure routine vaccinations are up to date', completed: true },
      { id: 'vax-4', text: 'Obtain International Certificate of Vaccination (yellow card)', completed: true },
      { id: 'vax-5', text: 'Pack vaccination card in carry-on luggage', completed: true },
    ],
    links: [
      { label: 'CDC Brazil Travel Health', url: 'https://wwwnc.cdc.gov/travel/destinations/traveler/none/brazil' },
      { label: 'WHO Vaccination Requirements', url: 'https://www.who.int/health-topics/vaccines-and-immunization' },
    ],
    completed: true,
    locked: false,
    order: 1,
    comments: [],
  },
  {
    id: 'packing',
    type: 'pre-trip',
    title: 'How to Pack',
    subtitle: 'What to Bring',
    icon: 'luggage',
    description: 'Packing essentials for your Brazil trip',
    detailedDescription: 'Pack light and smart for Rio de Janeiro and Ilha Grande! The weather will be warm and humid (summer in Brazil). You\'ll need beachwear, comfortable walking shoes, and some casual evening outfits.\n\nDon\'t forget essentials like sunscreen (SPF 50+), insect repellent, and a reusable water bottle. For Ilha Grande, pack a small daypack for hikes and quick-dry clothing.\n\nRemember: Brazilian outlets use Type N plugs (similar to Type C/Europlug). Bring an adapter if needed.',
    checklist: [
      { id: 'pack-1', text: 'Light, breathable clothing (shorts, t-shirts, sundresses)', completed: true },
      { id: 'pack-2', text: 'Swimwear and beach towel (or use hotel beach kit)', completed: true },
      { id: 'pack-3', text: 'Comfortable walking shoes + flip flops/sandals', completed: true },
      { id: 'pack-4', text: 'Sunscreen SPF 50+, sunglasses, and hat', completed: true },
      { id: 'pack-5', text: 'Insect repellent (especially for Ilha Grande)', completed: true },
      { id: 'pack-6', text: 'Rain jacket or light poncho (tropical showers)', completed: true },
      { id: 'pack-7', text: 'Power adapter for Brazil (Type N plug)', completed: true },
      { id: 'pack-8', text: 'Reusable water bottle', completed: true },
      { id: 'pack-9', text: 'Small daypack for excursions', completed: true },
      { id: 'pack-10', text: 'Casual evening outfit for dinners', completed: true },
      { id: 'pack-11', text: 'Medications and personal toiletries', completed: true },
      { id: 'pack-12', text: 'Copy of passport and travel insurance in carry-on', completed: true },
    ],
    links: [
      { label: 'Brazil Plug Type Guide', url: 'https://www.power-plugs-sockets.com/brazil/' },
      { label: 'Rio de Janeiro Weather Forecast', url: 'https://www.weather.com/weather/tenday/l/Rio+de+Janeiro+Brazil' },
    ],
    completed: true,
    locked: false,
    order: 2,
    comments: [],
  },
  {
    id: 'documents',
    type: 'pre-trip',
    title: 'Documents',
    subtitle: 'Travel Papers',
    icon: 'file-text',
    description: 'All travel documents you need for the trip',
    detailedDescription: 'Make sure you have all essential travel documents organized and easily accessible. Keep digital copies of everything in your phone and email, plus printed backups in your carry-on.\n\nParrot Trips will provide your hotel confirmations and activity vouchers. You are responsible for your passport, visa, vaccination records, travel insurance, and flight tickets.\n\nWe recommend keeping a folder with printed copies of all important documents separate from your originals.',
    checklist: [
      { id: 'doc-1', text: 'Valid passport (6+ months validity)', completed: true },
      { id: 'doc-2', text: 'Visa/eVisa approval printed', completed: true },
      { id: 'doc-3', text: 'Flight tickets/boarding passes', completed: true },
      { id: 'doc-4', text: 'Travel insurance document', completed: true },
      { id: 'doc-5', text: 'Vaccination card / Yellow Fever certificate', completed: true },
      { id: 'doc-6', text: 'Hotel reservation confirmations', completed: true },
      { id: 'doc-7', text: 'Emergency contact card', completed: true },
      { id: 'doc-8', text: 'Digital copies of all documents saved in phone/email', completed: true },
      { id: 'doc-9', text: 'Pre-Departure Form submitted to Parrot Trips', completed: true },
    ],
    links: [
      { label: 'Download Pre-Departure Form', url: '#' },
      { label: 'Travel Insurance Guide', url: '#' },
    ],
    attachments: [
      { name: 'Pre-Departure Checklist', type: 'PDF' },
      { name: 'Emergency Contacts Card', type: 'PDF' },
    ],
    completed: true,
    locked: false,
    order: 3,
    comments: [],
  },
];

export const tripDays: TripDay[] = [
  {
    id: 'day1',
    type: 'in-trip',
    title: 'Day 1 \u2014 Feb 27',
    subtitle: 'Arrival in Rio',
    icon: 'plane-landing',
    description: 'Airport pickup, Hotel Check-in, Ipanema Beach & Welcome Happy Hour',
    detailedDescription: 'Welcome to Rio de Janeiro! Get picked up from the airport, check into the Astoria Ipanema Hotel, explore Ipanema Beach, then join us for a Welcome Happy Hour at La Carioca En La Playa.',
    comments: [],
    completed: true,
    locked: false,
    order: 4,
    activities: [
      {
        id: 'a-airport-pickup',
        name: 'Airport Pickup',
        type: 'logistics',
        time: '10:00 AM',
        duration: '\u2014',
        description: 'We will pick you up on your arrival day according to the details provided in your Pre-Departure Form. To confirm your specific pickup time and group, please check the "View Details" section below.',
        practicalInfo: 'Airport Pickups & Arrivals\n\nFebruary 27th, 2026 (GIG Airport)\n\n  \n- 08:20 AM | Elie S. Mutomb, Jacqueline Barraza, Ivan Barrueta, Jasmin Lopez, Glenn Goist.\n\n  \n- 10:15 AM | Kristen Fernandez, Jonathan Pizano, Terry Winston, Dario Garcia.\n\n  \n- 12:00 PM | Bernardo Ferreira, Daniel Tineo, DeVar Jones.\n\n  \n- 02:30 PM | Isaiah Thomas Pihlstrom.\n\nFebruary 28th, 2026 (GIG Airport)\n\n  \n- 10:55 AM | Tyler Gray.\n\n  \n- 04:30 PM | Bailey Ethier, Abrahm Philip Coury.\n\nMarch 1st, 2026 (GIG Airport)\n\n  \n- 09:25 AM | Aaron Slater.',
        images: ['https://static.wixstatic.com/media/e340b3_ca732f1773e54c888606be94003cb864~mv2.jpg/v1/fill/w_1365,h_2048,al_c,q_90,enc_auto/PARROT%20TRIPS%202025_DIA%203-32%20(1).jpg'],
      },
      {
        id: 'a-checkin-rio',
        name: 'Hotel Check-in (Astoria Ipanema)',
        type: 'logistics',
        time: '2:00 PM',
        duration: '\u2014',
        description: 'Location\n- Hotel: Astoria Ipanema Hotel\n- Address: R. Visc. de Pirajá, 539 - Ipanema, Rio de Janeiro - RJ, 22410-003\n\nCheck-in Policy\n- Standard Check-in: From 02:00 PM onwards.\n- Early Arrivals: If you arrive before 02:00 PM and your room is not yet available for an early check-in, the hotel provides a secure luggage storage room.\n- While You Wait: You are welcome to use the hotel’s common areas or explore the beautiful Ipanema neighborhood nearby while we get your room ready.\n\nBreakfast Service\n-Time: 06:00 AM – 10:00 AM (Ground Floor).\n- Important Note: Seating is limited to 30 people at a time. We recommend arriving early during peak hours.',
        practicalInfo: 'Welcome to Astoria Ipanema Hotel, steps from Ipanema Beach. \n\n  \n- Expect a relaxed, beach-city vibe with a 24-hour gym, a rooftop for sunset views. \n\n  \n- Spa: by appointment—book at reception. \n\n  \n- Gym: open 24h. \n\n  \n- Rooftop: Fri–Sun 1:00PM - 09:00PM\n\n  \n- No pool, but you can ask for a beach kit at frontdesk (chair, towel...)\n\nLocal Tips & Essentials\n\n  \n- Hydration: Please note that bottled water in the hotel rooms is not complimentary and can be quite expensive.\n\n  \n- Money-Saving Tip: There is a Zona Sul Supermarket just a short walk away. We recommend stopping there to stock up on water and snacks at much lower prices.',
        images: ['https://static.wixstatic.com/media/d6fbec_eb31e83ed65248de8b7b1adfd8485aec~mv2.jpeg/image-rio-de-janeiro-mar-ipanema-hotel-98.jpeg'],
      },
      {
        id: 'a-ipanema',
        name: 'Enjoy Ipanema Beach',
        type: 'suggested',
        time: '3:00 PM',
        duration: '~2h',
        description: 'Our recommendation for today is to enjoy Ipanema Beach, located just two blocks from the hotel. If you want to explore a bit more, you can walk along Ipanema Beach until the Copacabana Fort and have a great view from this other famous beach, Copacabana! \n\nThis activity is completely optional and can be done at your own pace.\n\nGood to know:\n– You can rent beach chairs and umbrellas directly on the sand or get them from the hotel\n– Don’t leave your belongings unattended.\n– Take advantage of the amazing variety of snacks, drinks, and other items sold right on the beach — you’ll find almost anything you can imagine!',
        practicalInfo: '- Copacabana Fort location - Open from Tuesday to Sunday, from 10am to 7pm. There is an entrance fee and it can be paid directly at the gate\n\n  \n- Great restaurants around in Ipanema:\n\n- Babbo Osteria\n\n- Teva Bistrô (Vegan)\n\n- Zazá Bistrô Tropical\n\n- Pope Ipanema\n\n  \nSome nice things to know\n\n  \n- Ipanema Beach Guide Ipanema Beach is one of Rio de Janeiro’s most iconic places, known worldwide for its natural beauty, vibrant atmosphere, and deep cultural influence. \n\n  \n- Framed by the dramatic Dois Irmãos mountains and blessed with golden sand and turquoise water, Ipanema became famous in the 1960s with the bossa nova classic “The Girl from Ipanema.” Since then, it has remained a symbol of Rio’s relaxed lifestyle, breathtaking sunsets, and joyful beach culture. \n\n  \n- How to Spend the Day at Ipanema Beach A day at Ipanema is simple, effortless, and full of local traditions. When you arrive, you don’t need to bring much: beach vendors and small stands called barracas provide almost everything. You can easily rent beach chairs and umbrellas, and most stands offer drinks, snacks, and even Wi-Fi. \n\n  \n- The beach is divided into “postos,” numbered lifeguard stations that serve as reference points—each with its own personality and crowd. \n\n  \n- Locals spend hours lounging in the sun, swimming, playing frescobol (a type of paddleball), or simply people-watching. \n\n  \n- Just keep an eye on your belongings and bring only the essentials. \n\n  \n- The Unique Beach Vendor Culture One of the most charming aspects of Ipanema is its vibrant vendor culture. You’ll see sellers walking up and down the sand offering almost everything you might crave. The most traditional items include: - Mate Gelado: A refreshing iced tea served from metal barrels, usually mixed with fresh lemon. - Biscoito Globo: A crunchy, airy snack made of cassava flour — a true Rio classic. - Queijo Coalho: Skewered Brazilian cheese grilled right in front of you, often served with oregano. - Açai bowls, fresh fruit, caipirinhas, coconut water, and a variety of local snacks. - Beach wraps, hats, sunglasses, and even massages. \n\n  \n- This lively commerce is part of what makes the experience so special — you can spend the whole day enjoying the beach without ever needing to leave your chair.',
        images: ['https://static.wixstatic.com/media/08ee93_365268b28422488b92e2f5b224a746e7~mv2.jpg/vista-praia-de-ipanema-rio-de-janeiro.jpg'],
      },
      {
        id: 'a-happyhour',
        name: 'Welcome Happy Hour @ La Carioca En La Playa',
        type: 'included',
        time: '5:00 PM',
        duration: '~4h',
        description: '05:00 PM | Kick-off at the beach bar La Carioca En La Playa\n09:00 PM | Event concludes (perfect timing for dinner in Leblon).\n\nAddress: Av. Delfim Moreira, 117 – Posto 12, Leblon.\n\nGood to know:\n- Easy to walk from the hotel (10 min), or take Uber/taxi (5 min) — transportation not included.\n- This is a beach bar, a typical spot where Cariocas end their week with a drink. Expect local barefoot–bikini vibes. It’s totally fine to come straight from the beach!\n- Open bar included! (Caipirinha, beer, water, and soft drinks)\n- There will be some Brazilian finger foods (dinner not included).\n- We will also introduce our Parrot staff and share important information about the trip. You don\'t want to miss it!\n- There are many great dinner options in the Leblon neighborhood that you can walk or Uber/taxi to after the happy hour.',
        practicalInfo: 'In Rio de Janeiro, the beach is almost an extension of home, a ritual woven into the city’s rhythm. On Fridays, as soon as work ends, cariocas head straight to the sand, already with flip-flops and bikinis in their bags, to watch the sun set behind the Dois Irmãos mountain at Ipanema Beach. There, surrounded by friends, music, an iced mate or a cold beer, everyone slows down together. It’s more than a habit: it’s a simple, shared celebration that marks the start of the weekend in the most quintessentially carioca way.\n\nWe will experience some of this vibe as we welcome you to your first day in Brazil! We’ll be toasting at a beach bar right on the sand of Ipanema Beach while we watch the sunset. Feel free to wear whatever you like — even a bathing suit if you’d like to take a swim.\n\nYou’ll have the chance to try our local drink, the Caipirinha, made with lime, sugar, and cachaça, as well as our local draft beer (we call it chopp). We’ll also have some typical Brazilian appetizers (with vegetarian and vegan options available). We’ll wrap things up around 7pm, once the sun goes down. From the bar, you can head straight to dinner if you’d like (see recommendations below) or return to the hotel.\n\nDuring the event, we’ll also share some important information about the trip. It’s a great opportunity to meet the Parrot staff who will be with you throughout your journey. Feel free to ask any questions, we’re here to host you in our amazing country!!\n\nINCLUDED:\n\n  \n- Open Bar (Caipirinha, Beer, soft drinks)\n\n  \n- Brasilian Finger food\n\nNOT INCLUDED:\n\n  \n- Transportation\n\n  \n- Dinner\n\n  \n- Anything that is not metioned on the tour discription\n\n  \n- Gratuities and tips\n\nDinner Suggestions near by: \n\n  \n- CT Boucherie – A classic French-style steakhouse by chef Claude Troisgros. Famous for its perfectly cooked meats and the endless table-side “guarnições” (side dishes) that keep coming throughout the meal.\n\n  \n- Jobi – A beloved, lively Brazilian bar-restaurant that’s been a neighborhood icon for decades. Perfect for an authentic, casual carioca night with cold beer and delicious traditional food.\n\n  \n- Bráz Pizzaria – One of Rio’s best pizzerias, serving high-quality Neapolitan-style pizzas with Brazilian flair. Cozy, friendly, and perfect for a laid-back dinner.\n\n  \n- Sushi Leblon – One of Rio’s most iconic sushi restaurants. Trendy, always busy, and known for excellent fish quality, creative rolls, and a stylish atmosphere. A classic spot for sushi lovers.\n\n  \n- Nola – A cozy bistro with warm lighting and a contemporary menu inspired by international comfort food. Great cocktails, delicious small plates, and a relaxed, intimate vibe.\n\n  \n- Balcão 201 – A modern bar-restaurant with a long counter (the “balcão”) where guests can enjoy cocktails, wines, and flavorful dishes. Lively but refined — good for drinks that turn into dinner.\n\n  \n- TT Burger – A casual and delicious Brazilian-style burger joint by chef Thomas Troisgros. Famous for its juicy burgers, sweet potato fries, and the iconic “milk de brigadeiro” milkshake.\n\nOr \n\nBars on Rua Dias Ferreira:\n\nRua Dias Ferreira is one of Leblon’s liveliest streets — a true carioca hotspot. On Friday nights, locals gather here to drink, snack on Brazilian “petiscos,” and enjoy the buzzing, informal atmosphere. Expect people spilling onto the sidewalks, chatting, laughing, and enjoying live music. Very lively, very Rio. our favorites are: \n\n  \n- Belmonte Bar – A classic Rio bar serving great draft beer (“chopp”), savory pastries, and lots of traditional snacks. Always busy, always fun.\n\n  \n- Boa Praça Bar – Trendy, open-air, and full of young locals. A great spot for cocktails, cold beer, and people-watching — often packed and energetic.\n\n  \n- Rainha – A popular botequim-style bar known for its relaxed vibe, affordable drinks, and tasty bar food. Very local, very authentic, and great for a casual night.',
        images: ['https://static.wixstatic.com/media/08ee93_2b172e370be8445f9806e7fd98b771ac~mv2.jpg/477795577_602203619386447_5357425313557375628_n.jpg'],
      },
      {
        id: 'a-rio-recs',
        name: 'Our Rio Recommendations',
        type: 'suggested',
        time: 'Anytime',
        duration: '\u2014',
        description: 'Our curated selection of restaurants, bars, spas, and activities for your free time in Rio!',
        practicalInfo: '📍Do What Cariocas Do (By Bernardo)\n\n  \n- Juice Bars: Stop at Polis Sucos for a very typical juice or açaí experience.\n\n  \n- Ice Cream: Grab a gelato at Bacio di Latte, located right in front of your hotel.\n\n  \n- Don’t eat shrimp at the beach: All other beach snacks are usually safe, but avoid the shrimp skewers. \n\n  \n- The "Gringo" term: Don\'t find it weird if you are called a "Gringo". In Brazil, it simply means "foreigner"—it\'s not an insult!\n\n🍽️Restaurants Rio People Love\n\nBrazilian & Steakhouses\n\n  \n- Casa da Feijoada: Best place to eat the traditional bean stew called Feijoada.\n\n  \n- Assador Rio’s: Premium steakhouse with views of Guanabara Bay.\n\n  \n- Braseiro da Gávea: Very local steakhouse — expect long lines.\n\n  \n- Pura Brasa: Excellent meat, one of the best and super casual. By Bernardo \n\n  \n- Paz e Amor: Simple, traditional, and perfect for a quick, cheap bite. By Bernardo\n\nJapanese & Asian Fusion\n\n  \n- Gurumê / San Omakase: High-level, innovative Japanese dining. By Bernardo\n\n  \n- Jappa da Quitanda: Another great and popular sushi option. By Bernardo\n\nItalian (Fancier Options)\n\n  \n- Babbo, Nino, Posí, or Pici: All excellent Italian choices in the Ipanema/Leblon area. By Bernardo\n\nHealthy & Vegan\n\n  \n- Teva: The best vegan restaurant in Rio — highly recommended for everyone! By Bernardo\n\n  \n- Delírio Tropical: Great spot for fresh, healthy food. By Bernardo\n\n  \n- Nusa Café: Excellent for a healthy breakfast or brunch. By Bernardo\n\nOther Must-Trys\n\n  \n- La Carioca: Known for great ceviche (same vibe as our Welcome Event). By Bernardo\n\n  \n- Oro: 2-Michelin-star restaurant blending Brazilian roots with cutting-edge technique.\n\n  \n- TT Burger: Rio’s most famous gourmet burger.\n\n🍻Classic Bars Cariocas Always Go To\n\n  \n- Boteco Belmonte (Ipanema): A classic Rio bar — cold draft beer and traditional snacks. By Bernardo\n\n  \n- Boteco Boa Praça (Ipanema): Another famous Rio bar, often with live music.\n\n  \n- Spirit Copa (Copacabana): Fancy and pricey venue with great food and impressive views of Copacabana.\n\n  \n- Bafo da Prainha (Center): Very local, roots bar near Pedra do Sal.\n\n  \n- VuVu Lounge (Botafogo): Innovative bar-lounge with Japanese–Peruvian fusion food, special gin-based cocktails, and live shows. Famous for forró on Tuesdays and parties on Fridays.\n\n  \n- Beco Das Garrafas: Entitled as the Bossa Nova birth place, live shows everyday\n\nStreets with Many Good Bars (Very Local)\n\n  \n- Dias Ferreira Street (Leblon): Packed with bars and people; most popular at night.\n\n  \n- Rua do Senado (Center): Voted one of the “coolest streets in the world” by Time Out; best on Saturdays and Sundays.\n\n  \n- Arnaldo Quintela Street (Botafogo): One of the liveliest bar streets in the city.\n\n  \n- Nelson Mandela Street (Botafogo): Casual bars, football on TV, and a very local vibe.\n\n🛍️General Shopping\n\n  \n- Shopping Leblon: A sophisticated mall within walking distance. Great for well-known Brazilian brands. By Bernardo\n\n  \n- Zona Sul Supermarket: Excellent grocery store. There are two very close to the hotel—perfect for buying water and snacks. By Bernardo\n\n✨Taking the Time to Relax: Spas & Massage\n\n  \n- Fasano Hotel Spa: The best spa in the area and very close to our hotel. High-end experience and on the pricier side.\n\nhttps://www.fasano.com.br/en/facilities/fasano-rio-de-janeiro-spa/\n\n  \n- Buddha Spa (Ipanema): A great, more affordable option for massages and treatments.\n\nhttps://buddhaspa.com.br/unidades/ipanema/\n\n(Website is in Portuguese, but you can easily book via WhatsApp.)\n\n🏛️Touristing On Your Own\n\nGreat places you can visit without a guide.\n\n  \n- Botanical Garden (Jardim Botânico do Rio): A calm escape with towering imperial palms, orchids, and shaded paths — perfect for a mid-afternoon walk before evening plans.\n\n  \n- Museum of Tomorrow (Praça Mauá): A striking, future-focused science museum on the waterfront, with immersive exhibitions about the planet, sustainability, and our choices ahead.\n\n  \n- Parque Lage: Historic park at the foot of Corcovado with gardens, a mansion, and access to Tijuca Forest trails — great for photos, coffee, and an easy stroll.\n\n  \n- Parque das Ruínas (Santa Teresa): Open-air ruins with panoramic views over downtown Rio and Guanabara Bay, often hosting cultural events and exhibitions.\n\n  \n- Forte de Copacabana: Historic fort at the edge of Copacabana Beach with ocean views, small museums, and one of the best spots in the city for breakfast or coffee by the sea.\n\n  \n- Walking Ipanema & Leblon Beaches: Walk the beachfront, explore side streets, stop for coconut water or coffee, and soak in everyday carioca life.\n\nWhat to do in Rio on a rainy day ☔️🌴\n\n1. Visit the Museum of Tomorrow (Museu do Amanhã) \n\n🎟 Tickets: https://bileto.sympla.com.br/event/114011/d/353321\n\n2. Go shopping at Shopping Leblon 🛍️\n\n 📍 : https://maps.app.goo.gl/UxBivJMr54yfhZdL9\n\n3. Take shelter at a classic Rio bar 🍻 Like Belmonte or Boa Praça (both in Ipanema).',
        images: ['https://static.wixstatic.com/media/e340b3_3cf99d843ea44ff69b05fbef17bd9f4f~mv2.jpg/feira%20da%20gloria.jpg'],
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day2',
    type: 'in-trip',
    title: 'Day 2 \u2014 Feb 28',
    subtitle: 'BBQ & Rio Nightlife',
    icon: 'flame',
    description: "Brazilian Barbecue at Bernardo's & explore Rio nightlife",
    detailedDescription: "Experience an authentic Brazilian barbecue (churrasco) hosted by Bernardo, then explore Rio's legendary nightlife scene.",
    comments: [],
    completed: true,
    locked: false,
    order: 5,
    activities: [
      {
        id: 'a-bbq',
        name: "Barbecue @ Bernardo's",
        type: 'included',
        time: '1:00 PM',
        duration: '~3h',
        description: 'More details coming soon!',
        practicalInfo: 'Transfer from hotel included. Casual dress code. Vegetarian options available.',
        images: ['https://static.wixstatic.com/media/11062b_1df313c619eb4b44bb26f551a093ea0e~mv2.jpg/Barbecue%20Grill%20Fire.jpg'],
      },
      {
        id: 'a-bars',
        name: 'Explore Local Bars & Parties',
        type: 'suggested',
        time: '9:00 PM',
        duration: 'Evening',
        description: "Explore Rio's vibrant nightlife! From the iconic bars of Lapa to the trendy spots of Leblon.",
        practicalInfo: 'Check Our Rio Recommendations for the best spots. Travel in groups and keep valuables secure.',
        images: ['https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=600&h=400&fit=crop'],
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day3',
    type: 'in-trip',
    title: 'Day 3 \u2014 Mar 1',
    subtitle: 'Christ & Sugarloaf',
    icon: 'mountain',
    description: 'Bike Tour, Christ the Redeemer & Sugarloaf Mountain + Samba @ Bosque Bar',
    detailedDescription: "Optional morning bike tour, then visit two of Rio's most iconic landmarks \u2014 Christ the Redeemer and Sugarloaf Mountain. In the evening, catch a samba party at Bosque Bar.",
    comments: [],
    completed: false,
    locked: false,
    order: 6,
    activities: [
      {
        id: 'a-biketour',
        name: 'Bike Tour',
        type: 'optional',
        time: '9:00 AM',
        duration: '~3h',
        description: '- Tour time is 3 hours. In total we bike around 2 hours.\n- Includes: Bike – Helmet – Guide\n - Bring water!!',
        practicalInfo: 'Pedal the beachfront cycle paths that link Copacabana and Ipanema—flat, scenic lanes made for an easy, sea-breeze ride (including the Arpoador stretch). Then cruise the multi-use path around Lagoa Rodrigo de Freitas, a near-level loop of about 7–7.7 km framed by hills and palm-lined shores. Expect postcard views and a relaxed pace on mostly dedicated bike lanes—an effortless way to tap into Rio’s everyday outdoor vibe.',
        images: ['https://static.wixstatic.com/media/5c464c_99d349fbac0b4491812d35adfcea81a8~mv2.webp/IMG_9561%20(1).webp'],
      },
      {
        id: 'a-christ',
        name: 'Christ the Redeemer & Sugarloaf',
        type: 'included',
        time: '7:30 AM',
        duration: '~6h',
        description: '07:30 AM | Departure from the Astoria Hotel Lobby.\n01:00 PM | Estimated return to the hotel.\n\nPlaces we will visit: Christ the Redeemer and the SugarLoaf. \n\nGood To know: \n- Bring a small day-pack with water, sunscreen, sunglasses, and a hat (or bucket hat).\n- We recommend light, breathable clothing and comfortable walking shoes. There are a few steps and some walking involved at both sites.\n- Hike opportunity: On our second stop, Sugarloaf, it\'s possible to do a 40 minutes hike up to the first hill (Urca) and from there get a cable car to the Sugarloaf mountain. \n- Check the forecast! If there is a chance of rain, we highly recommend bringing a light rain jacket.',
        practicalInfo: 'See Rio from its most iconic viewpoints! Visit the towering Christ the Redeemer and ride the Sugarloaf cable car for panoramic city views.\n\nChrist the Redeemer & Corcovado Train \n\n  \n- We begin aboard the Corcovado rack railway, inaugurated in 1884 and electrified in 1910—the first electrified railroad in Brazil—climbing through Tijuca National Park to the 700 m summit. \n\n  \n- At the top, you’ll meet the world-famous Art Deco statue, completed in 1931: 30 m tall (38 m including the pedestal), arms spanning 28 m, built of reinforced concrete with a soapstone veneer, designed and engineered by Heitor da Silva Costa (with Albert Caquot) and sculpted in part by Paul Landowski (face by Gheorghe Leonida). \n\nSugarloaf (Pão de Açúcar) & Cable Car \n\n  \n- For our second stop, we head to Urca for the two-stage cable car: Praia Vermelha → Morro da Urca → Sugarloaf. \n\n  \n- Rio’s cableway opened its first section in 1912 and is presented by the park as the oldest operating cable car in the world—two historic cabins (1912 and 1972) are on display at Cable Car Square. \n\n  \n- Sugarloaf’s name dates to the 16th-century Portuguese sugar trade, when refined sugar was shipped in conical “loaves” whose shape the mountain resembles; the peak rises 396 m at the mouth of Guanabara Bay and is part of Rio’s UNESCO-listed landscape. \n\n  \n- Each stop offers viewpoints, short walks, and cafés with bay-to-ocean panoramas. \n\nINCLUDED:  \n\n  \n- Tickets to Christ the redeemer train and entrance Fast Pass tickets to the Sugarloaf cable car and entrance  \n\n  \n- Tranportation \n\nNOT INCLUDES:  Anything that is not metioned on the tour discription',
        images: ['https://static.wixstatic.com/media/5c464c_ed1255180692453c804a86dfbeee96bb~mv2.webp/PARROT%20TRIPS%202025_DIA%202_-22.webp'],
        vibe: 'Sightseeing',
      },
      {
        id: 'a-samba-bosque',
        name: 'Samba Party @ Bosque Bar',
        type: 'suggested',
        time: '8:00 PM',
        duration: 'Evening',
        description: 'This is Rio\'s official Sunday party!  “Sambinha do Bosque” is a Sunday samba/pagode party with live acts and DJs. Samba and pagode are Brazilian music styles. \n\nTotally optional—join if you feel like it! \n\nThere’s a TT Burger inside if you want a bite.',
        practicalInfo: '- Bosque Bar — Sambinha do Bosque (8:00 PM) Bosque Bar is a venue inside the Jockey Club area in Gávea (Av. Bartolomeu Mitre, 1314). It\'s Sunday\'s official party place in Rio\n\n  \n- It’s known for live music, DJs, easy access/parking, and a relaxed vibe—great for a casual night out. \n\n  \n- How it works “Sambinha do Bosque” is a Sunday samba/pagode party with live acts and DJs. Samba and pagode are Brazilian music styles. \n\n  \n- Doors open in the evening; for our group, we suggest 8:00 PM. \n\n  \n- Expect standing areas with some lounge spots. \n\n  \n- Tickets Buy online via Ingresse. Some listings require the digital ticket in the Ingresse app and note that late arrivals after door-closing may be denied entry—so plan to arrive on time.. \n\n  \n- Food & drinks There’s TT Burger inside for a quick bite, plus a full bar. \n\n  \n- Tips Bring a photo ID (events are typically 18+), dress casual, and consider ride-share for convenience. \n\n  \n- If it sells out, door sales may close early.',
        images: ['https://static.wixstatic.com/media/e340b3_8ce79096bd3540fa9e9ba89822e924fb~mv2.png/bosque%20bar.png'],
        vibe: 'Gathering',
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day4',
    type: 'in-trip',
    title: 'Day 4 \u2014 Mar 2',
    subtitle: 'Historic Center & Samba',
    icon: 'landmark',
    description: 'SUP at Sunrise, Historic Center Tour, Footvolley & Pedra do Sal',
    detailedDescription: "Optional sunrise paddleboarding, then explore Rio's historic center with an expert guide. Afternoon footvolley class and evening samba at Pedra do Sal.",
    comments: [],
    completed: false,
    locked: false,
    order: 7,
    activities: [
      {
        id: 'a-sup',
        name: 'Stand Up Paddle at Sunrise (Copacabana)',
        type: 'optional',
        time: '4:30 AM',
        duration: '~2h',
        description: 'Departure: 4:00 AM from hotel — please be on time!\nPaddling time: from 4:40 to 5:40 (☀ Sunrise at 5:10 AM)\nEstimates return time: 6:30am\n\nDifficulty leve: Easy to moderate \nVisited places: Copacabana beach \n\nGood to know:\n- Be on time at the meeting point\n-There is a luggage storage but bring only the essential \n-Wear sunscreen, hat and sunglasses \n-Life jackets are mantory and will be provided by the crew',
        practicalInfo: 'Paddle the calm waters of Posto 6 by the Copacabana Fort—one of Rio’s classic SUP spots known for gentle conditions and scenic views. Sessions usually begin with a quick on-shore briefing on balance and paddling before you launch with an instructor nearby. Sunrise times are especially popular for smoother seas and softer light along Copacabana’s curve.\n\nIncluded:\n1 board per person\nLuggage storage\nWarm-up session\nPaddling instruction\nSUP equipment: life jacket, paddle, board\nThe tour takes place even in cloudy weather. In cases of rain, strong winds, high tide, or rough seas, the tour will be canceled and the activity fee refunded.',
        images: ['https://static.wixstatic.com/media/5c464c_f45b992ec6894d808470365f72dc9f02~mv2.webp/edb07a4a-6a82-4ea0-a4d2-e33d0faaf218%20(1).webp'],
        vibe: 'Outdoor',
      },
      {
        id: 'a-historic',
        name: 'Historic Center Tour',
        type: 'included',
        time: '9:00 AM',
        duration: '~4h',
        description: '09:00 AM| Departure from the Astoria Hotel Lobby.\n01:00 PM | Estimated return to the hotel.\n\nExplore Rio’s historical landmarks with an expert local guide.\n\nGood to Know\n- For your comfort and safety, please wear comfortable closed-toe shoes (sneakers are ideal). Expect to navigate hills, stairs, and traditional cobblestone streets.\n- We recommend bringing a small day-pack with sunscreen, a hat, and a bottle of water.\n- It is useful to have some local currency (cash) for small purchases or snacks along the way.\n- To ensure the best experience, please stay close to your guide at all times.\n- Punctuality: To make the most of our itinerary, please be at the meeting point by 08:50 AM.',
        practicalInfo: "Explore Rio's historical landmarks with an expert local guide. Walk through colonial streets, visit churches, see the Royal Portuguese Reading Room.",
        images: ['https://static.wixstatic.com/media/e340b3_4f87b0d9df2049c991a251bb33eaad16~mv2.jpg/PARROT%20TRIPS%202025_DIA%203-6.jpg'],
        vibe: 'Outdoor',
      },
      {
        id: 'a-footvolley',
        name: 'Footvolley Class',
        type: 'optional',
        time: '3:00 PM',
        duration: '~1h',
        description: 'Time to go really deep into the Carioca culture, playing foot volley in Ipanema beach.\n\n1 hour class\n\n Wear light sportswear, swimwear, or clothes you don\'t mind getting sandy.\n\nSunscreen and a bottle of water are highly recommended. \n\nLocation and further instructions will be sent closer to the date',
        practicalInfo: '-  Classes are structured to accommodate all levels, from complete beginners to intermediate players. \n\n  \n- The instructor will provide drills and friendly game scenarios to practice new skills. \n\n  \n- In case of heavy rain or storms, the activity may be canceled and the fee refunded. \n\n  \n- Included: - Professional instructor, footvolley balls,  marked court/net setup',
        images: ['https://static.wixstatic.com/media/7693bd_81817979b2fe4fc1a8bad262557905c7~mv2.webp/futevolei.webp'],
        vibe: 'Outdoor',
      },
      {
        id: 'a-pedradosal',
        name: 'Samba da Pedra do Sal',
        type: 'included',
        time: '6:30 PM',
        duration: '~5h',
        description: 'The purest Brazilian juice \u2014 popular, open-air samba music, known as the birthplace of Samba! Monday is the most famous day.',
        practicalInfo: '- Pedra do Sal is located here but the dropp off point is the Largo de São Francisco da Prainha\n\n  \n- It is a historical heritage site and the birthplace of urban samba in Rio. It’s an open-air street party, known for its deep cultural roots, live acoustic samba, and a very casual, energetic crowd. \n\n  \n- How it works The "Roda de Samba" happens at the foot of the rock, where musicians gather around a table to play classics. The crowd stands around them, singing and dancing. It usually happens on Monday nights (the traditional one) and sometimes Fridays. \n\n  \n- Expect a packed street, standing room only, and a vibrant, communal atmosphere. \n\nGood to know: \n\n  \n- Tickets No tickets required.\n\n  \n-  It is a public street event and completely free to enter. \n\n  \n-  There are no formal waiters. You buy drinks (beers, caipirinhas) and food (street BBQ, pastries) from the many street vendors and tents scattered around the area. \n\n  \n- Bring cash as some vendors might not take cards, though many do. - \n\n  \n- Safety: It gets very crowded. Keep your phone and wallet in front pockets or a fanny pack; avoid wearing expensive jewelry. \n\n  \n- Dress code: Very casual. Wear comfortable shoes (sneakers) as the ground is uneven/cobblestone and you will be standing. \n\n  \n- Transport: We highly recommend using Uber/rideshare to get there and back',
        images: ['https://static.wixstatic.com/media/7693bd_0197d7e6df05465f8db34296c0a6fde2~mv2.webp/Pedra-do-Sal-Rio-de-Janeiro.webp'],
        vibe: 'Gathering',
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day5',
    type: 'in-trip',
    title: 'Day 5 \u2014 Mar 3',
    subtitle: 'Beach & Dois Irm\u00e3os',
    icon: 'sun',
    description: 'Beach time, Dois Irm\u00e3os Hike & Favela Vidigal Tour',
    detailedDescription: "Relaxed morning at the beach, then hike to the top of Dois Irm\u00e3os for one of the best views in Rio, passing through Vidigal Favela.",
    comments: [],
    completed: false,
    locked: false,
    order: 8,
    activities: [
      {
        id: 'a-beach',
        name: 'Beach Time',
        type: 'suggested',
        time: '9:00 AM',
        duration: '~3h',
        description: "Enjoy the morning at Ipanema or Copacabana beach! Soak in the sun and experience Rio's legendary beach culture.",
        practicalInfo: "The hotel is steps from Ipanema beach. Bring sunscreen, hat, and cash for beach vendors.",
        images: ['https://images.unsplash.com/photo-1476673160081-cf065607f449?w=600&h=400&fit=crop'],
      },
      {
        id: 'a-doisirmaos',
        name: 'Dois Irm\u00e3os Hike & Favela Vidigal Tour',
        type: 'included',
        time: '1:30 PM',
        duration: '~4.5h',
        description: "Hike up the Dois Irm\u00e3os trail and enjoy one of the best views in Rio. Pass through Vidigal Favela.",
        practicalInfo: '- How this activity will be: \n\n- We will leave the hotel by 1:30PM \n\n- Meet our local favela guide at the botton part of the favela Vidigal \n\n- Get a another transfer ( a local favela van) up to the hiking starting point \n\n- Hike up then down \n\n- Walk down the Favela \n\n  \n- The trail is steep in parts, but the view from the top is one of the most rewarding in Rio. \n\n  \n- The total duration of the hike (up and down) is approximately 3 to 4 hours hours, depending on the group\'s pace.\n\n  \n- Come with proper hike clothing and comfortable shoes. Bring sunscreem and water\n\n  \n- In case of rain: we will assess the with the guide what is possible to do and update everyone.',
        images: ['https://static.wixstatic.com/media/7693bd_e3c1b51b1bfc4febba07f0338297e88c~mv2.avif/trilha-dois-irmaos.avif'],
        vibe: 'Sightseeing',
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day6',
    type: 'in-trip',
    title: 'Day 6 \u2014 Mar 4',
    subtitle: 'Rio \u2192 Ilha Grande',
    icon: 'ship',
    description: 'Transfer to Ilha Grande Island & Brazilian Dance Class',
    detailedDescription: 'Say goodbye to Rio and journey to the paradise island of Ilha Grande! Bus + boat transfer, beachfront hotel, and Forr\u00f3 dance lesson.',
    comments: [],
    completed: false,
    locked: false,
    order: 9,
    activities: [
      {
        id: 'a-transfer-ilha',
        name: 'Departure to Ilha Grande (Bus + Boat)',
        type: 'logistics',
        time: '8:00 AM',
        duration: '~5h',
        description: 'Journey from Rio to Ilha Grande island. ~3 hours driving + 1-hour boat ride.',
        practicalInfo: '- We depart from the Astoria Hotel at 08:00 AM, arriving at the Conceição de Jacareí pier by 11:00 AM. From there, we will proceed by boat to Ilha Grande.',
        images: ['https://static.wixstatic.com/media/e340b3_430325a3ce6f4867b451e82f68a4386a~mv2.jpeg/WhatsApp%20Image%202025-08-12%20at%2016.21.22.jpeg'],
        vibe: 'Transfer',
      },
      {
        id: 'a-checkin-ilha',
        name: 'Hotel Check-in (Recreio Da Praia)',
        type: 'logistics',
        time: '2:00 PM',
        duration: '\u2014',
        description: 'Check into the Recreio Da Praia hotel on Ilha Grande.',
        practicalInfo: 'Check-in: From 02:00 PM. Have ID/Passport handy.\nBreakfast: 07:00 AM \u2013 10:00 AM\n\nIsland Tips: Buy water at local "mercadinhos" (cheaper).',
        images: ['https://static.wixstatic.com/media/e340b3_4bf232eb627d4d289f3c8768307db329~mv2.avif/recreio%20da%20praia.avif'],
        vibe: 'Hotel',
      },
      {
        id: 'a-dance',
        name: 'Forr\u00f3 Dance Lesson & Caipirinha Workshop',
        type: 'included',
        time: '5:00 PM',
        duration: '2h',
        description: 'Immerse yourself in the authentic rhythms and flavors of Brazil! Energetic Forr\u00f3 dance lesson followed by a hands-on Caipirinha mixology workshop.',
        practicalInfo: 'Highlights\n\n  \n- Exclusive Privacy: A private boat tour dedicated entirely to our group.\n\n  \n- Scenic Swim Stops: 2 to 3 stops at breathtaking spots for swimming and snorkeling.\n\n  \n- Premium Inclusions: Lunch served onboard and a full Open Bar featuring authentic caipirinhas and cold beer.',
        images: ['https://static.wixstatic.com/media/e340b3_7f0a22b252f346c7abe0453b618f15e6~mv2.jpg/pexels-drethousand-8571178%20(1).jpg'],
        vibe: 'Culture',
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day7',
    type: 'in-trip',
    title: 'Day 7 \u2014 Mar 5',
    subtitle: 'Boat Ride',
    icon: 'sailboat',
    description: 'Private boat ride around Ilha Grande with swim stops & lunch',
    detailedDescription: 'The highlight of Ilha Grande! Private boat tour with swim stops, snorkeling, lunch onboard, and open bar.',
    comments: [],
    completed: false,
    locked: false,
    order: 10,
    activities: [
      {
        id: 'a-boat',
        name: 'Private Boat Ride',
        type: 'included',
        time: '10:30 AM',
        duration: '~6.5h',
        description: 'Exclusive private boat tour dedicated entirely to our group. 2\u20133 scenic swim stops for swimming and snorkeling, lunch onboard, open bar with caipirinhas and cold beer.',
        practicalInfo: '10:30 AM | Meet in Hotel Lobby.\\n11:00 AM | Boat Departure.\\n05:00 PM | Return to pier.\\n\\nBring towel, sunscreen, hat, sunglasses. Non-slip sandals recommended.',
        images: ['https://static.wixstatic.com/media/e340b3_7f0a22b252f346c7abe0453b618f15e6~mv2.jpg'],
        vibe: 'Outdoor',
      },
      {
        id: 'a-freenight',
        name: 'Free Night',
        type: 'suggested',
        time: '7:00 PM',
        duration: 'Evening',
        description: 'Free evening on the island! Explore village restaurants, grab drinks at a beach bar, or relax.',
        practicalInfo: 'The village has several restaurants and bars within walking distance.',
        images: [],
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day8',
    type: 'in-trip',
    title: 'Day 8 \u2014 Mar 6',
    subtitle: 'Beach & Goodbye Dinner',
    icon: 'palmtree',
    description: 'Free beach day, optional canoeing/hike & farewell dinner',
    detailedDescription: "A relaxed day to enjoy Ilha Grande at your own pace \u2014 then the unforgettable Goodbye Dinner at Bonito Para\u00edso restaurant.",
    comments: [],
    completed: false,
    locked: false,
    order: 11,
    activities: [
      {
        id: 'a-freebeach',
        name: 'Free Beach Day',
        type: 'suggested',
        time: '9:00 AM',
        duration: 'Full day',
        description: "Enjoy Ilha Grande's stunning beaches at your own pace.",
        practicalInfo: 'Beaches near the village are easily accessible on foot. Water taxis available for remote beaches.',
        images: ['https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&h=400&fit=crop'],
      },
      {
        id: 'a-canoe',
        name: 'Optional: Canoeing or Hike',
        type: 'optional',
        time: 'Flexible',
        duration: '~2\u20133h',
        description: "For the adventurous! Rent a canoe to explore the coastline or take one of the island's hiking trails.",
        practicalInfo: 'Canoe rentals available at the main pier. Ask the team for recommended trails.',
        images: ['https://images.unsplash.com/photo-1472745942893-4b9f730c7668?w=600&h=400&fit=crop'],
      },
      {
        id: 'a-goodbye',
        name: 'Goodbye Dinner',
        type: 'included',
        time: '7:30 PM',
        duration: '~3h',
        description: 'The Grand Finale! Farewell dinner at Bonito Para\u00edso restaurant.',
        practicalInfo: '07:30 PM | Departure from the Pier.\n07:45 PM | Arrival at Bonito Para\u00edso.\n\nDress code: Smart casual.',
        images: ['https://static.wixstatic.com/media/e340b3_af6d6414168843f4a4883ed70cddfca4~mv2.jpg'],
        vibe: 'Outdoor',
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day9',
    type: 'in-trip',
    title: 'Day 9 \u2014 Mar 7',
    subtitle: 'Return to Rio',
    icon: 'bus',
    description: 'Return to Rio de Janeiro via boat + bus',
    detailedDescription: 'Journey back from Ilha Grande to Rio with a boat ride, bus transfer, and airport drop-offs.',
    comments: [],
    completed: false,
    locked: false,
    order: 12,
    activities: [
      {
        id: 'a-return',
        name: 'Return to Rio de Janeiro (Boat + Bus)',
        type: 'logistics',
        time: '10:00 AM',
        duration: '~6h',
        description: 'Journey back from Ilha Grande to Rio. Scenic boat ride + bus transfer with airport drop-off.',
        practicalInfo: 'GIG Airport Drop-off\n\nFor travelers departing today, the transfer will stop at GIG Airport before continuing to the Astoria Hotel.\n\nScheduled Travelers for GIG:\n\n  \n- Flight at 10:55 PM: Jacqueline Barraza, Ivan Barrueta, Jasmin Lopez, and Tyler Gray.\n\nEstimated Arrival at GIG: Approximately 04:00 PM, allowing ample time for check-in and security.',
        images: ['https://static.wixstatic.com/media/e340b3_430325a3ce6f4867b451e82f68a4386a~mv2.jpeg/WhatsApp%20Image%202025-08-12%20at%2016.21.22.jpeg'],
        vibe: 'Transfer',
      },
    ],
    albumPhotos: [],
  },
  {
    id: 'day10',
    type: 'in-trip',
    title: 'Day 10 \u2014 Mar 8',
    subtitle: 'Departure',
    icon: 'plane',
    description: 'Airport transfers \u2014 until next time!',
    detailedDescription: 'The final day! Airport transfers arranged according to your departure form. Safe travels!',
    comments: [],
    completed: false,
    locked: false,
    order: 13,
    activities: [
      {
        id: 'a-airport',
        name: 'Transfer to Airport',
        type: 'logistics',
        time: '4:00 PM',
        duration: '~1.5h',
        description: 'Group transfer from Astoria Ipanema to GIG International Airport.',
        practicalInfo: 'Airport Drop-offs & Departures\n\nMarch 8th, 2026\n\n  \n- 04:00 PM | Hotel Pickup: Group transfer from Astoria Ipanema to GIG Airport for the following travelers:\n\nFlight at 08:00 PM: Kristen Fernandez, Jonathan Pizano, Bernardo G. C. G. Ferreira, Daniel Tineo, and DeVar Jones.\n\nFlight at 09:30 PM: Terry Winston, Isaiah Thomas Pihlstrom, and Dario Garcia.\n\nFlight at 10:55 PM: Bailey Ethier and Abrahm Philip Coury.',
        images: ['https://static.wixstatic.com/media/e340b3_ca732f1773e54c888606be94003cb864~mv2.jpg/v1/fill/w_1365,h_2048,al_c,q_90,enc_auto/PARROT%20TRIPS%202025_DIA%203-32%20(1).jpg'],
        vibe: 'Flight',
      },
    ],
    albumPhotos: [],
  },
];

export const currentUserId = '1';
export const currentUserPhaseId = 'day3';
export const parrotPhaseId = 'day3';

export const tripName = 'Bernardo Brazil Trip';
export const tripDates = 'Feb 27 \u2014 Mar 8, 2026';

export function getAllPhases(): (Phase | TripDay)[] {
  return [...preTripPhases, ...tripDays].sort((a, b) => a.order - b.order);
}

export function getPhaseById(id: string): Phase | TripDay | undefined {
  return getAllPhases().find(p => p.id === id);
}

export function getTravelersAtPhase(phaseId: string): Traveler[] {
  return travelers.filter(t => t.currentPhaseId === phaseId);
}

export function getProgressPercentage(phaseId: string): number {
  const allPhases = getAllPhases();
  const idx = allPhases.findIndex(p => p.id === phaseId);
  if (idx === -1) return 0;
  return Math.round(((idx + 1) / allPhases.length) * 100);
}

export function isTripDay(phase: Phase | TripDay): phase is TripDay {
  return phase.type === 'in-trip' && 'activities' in phase;
}

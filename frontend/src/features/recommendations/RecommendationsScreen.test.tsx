import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import { server } from '../../test/server';
import RecommendationsScreen from './pages/RecommendationsScreen';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

function renderRecommendationsScreen() {
  return render(
    <MemoryRouter>
      <RecommendationsScreen />
    </MemoryRouter>
  );
}

describe('RecommendationsScreen', () => {
  beforeEach(() => {
    navigateMock.mockClear();
  });

  test('renders rich recommendations from the backend and filters by category', async () => {
    server.use(
      http.get('http://localhost:8000/me/recommendations', () => HttpResponse.json({
        recommendations: [
          {
            id: 'rec-1',
            name: 'Babbo Osteria',
            description: 'Upscale Italian cuisine',
            address: 'Rua Barao da Torre, Ipanema',
            photo_url: null,
            sort_order: 1,
            category: 'restaurants',
            neighborhood: 'Ipanema',
            location: 'rio',
            highlight: 'Near the hotel',
            price_range: '$$$',
            rating: 4.7,
            map_url: 'https://maps.example/babbo',
            emoji: '🍝',
            phone: '+5521999999999',
            whatsapp_url: 'https://wa.me/5521999999999',
            contact_label: 'Concierge',
          },
          {
            id: 'rec-2',
            name: 'Ipanema Beach',
            description: 'Classic Rio beach',
            address: 'Ipanema, Rio de Janeiro',
            photo_url: null,
            sort_order: 2,
            category: 'beaches',
            neighborhood: 'Ipanema',
            location: 'rio',
            highlight: 'Steps from hotel',
            price_range: null,
            rating: null,
            map_url: null,
            emoji: '🏖️',
            phone: null,
            whatsapp_url: null,
            contact_label: null,
          },
        ],
      }))
    );

    renderRecommendationsScreen();

    expect(await screen.findByText('Babbo Osteria')).toBeInTheDocument();
    expect(screen.getByText('Ipanema Beach')).toBeInTheDocument();
    expect(screen.getByText('Near the hotel')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /call concierge/i })).toHaveAttribute('href', 'tel:+5521999999999');
    expect(screen.getByRole('link', { name: /whatsapp concierge/i })).toHaveAttribute('href', 'https://wa.me/5521999999999');

    await userEvent.click(screen.getByRole('button', { name: /beaches/i }));

    expect(screen.queryByText('Babbo Osteria')).not.toBeInTheDocument();
    expect(screen.getByText('Ipanema Beach')).toBeInTheDocument();
  });

  test('builds filters from wedding recommendation data and shows visual fallback without photos', async () => {
    server.use(
      http.get('http://localhost:8000/me/recommendations', () => HttpResponse.json({
        recommendations: [
          {
            id: 'rec-1',
            name: 'Aulas de Kitesurf - Professor Bete',
            description: 'Kitesurf lessons',
            address: 'Prea, Cruz - CE',
            photo_url: null,
            sort_order: 1,
            category: 'Esportes',
            neighborhood: 'Prea',
            location: 'Prea, CE',
            highlight: null,
            price_range: '$$$',
            rating: null,
            map_url: null,
            emoji: 'kite',
            phone: '+5588996439775',
            whatsapp_url: 'https://wa.me/5588996439775',
            contact_label: 'Professor Bete',
          },
          {
            id: 'rec-2',
            name: 'Balcon',
            description: 'Recommended restaurant in Prea',
            address: 'Prea, Cruz - CE',
            photo_url: null,
            sort_order: 2,
            category: 'Restaurantes',
            neighborhood: 'Prea',
            location: 'Prea, CE',
            highlight: null,
            price_range: '$$',
            rating: null,
            map_url: null,
            emoji: 'restaurant',
            phone: null,
            whatsapp_url: null,
            contact_label: null,
          },
        ],
      }))
    );

    renderRecommendationsScreen();

    expect(await screen.findByRole('button', { name: /prea, ce/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sports/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /restaurants/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /esportes/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /restaurantes/i })).not.toBeInTheDocument();
    expect(screen.getAllByTestId('recommendation-visual-fallback')).toHaveLength(2);

    await userEvent.click(screen.getByRole('button', { name: /restaurants/i }));

    expect(screen.queryByText('Aulas de Kitesurf - Professor Bete')).not.toBeInTheDocument();
    expect(screen.getByText('Balcon')).toBeInTheDocument();
  });

  test('lets travelers go back to the previous page', async () => {
    server.use(
      http.get('http://localhost:8000/me/recommendations', () => HttpResponse.json({ recommendations: [] }))
    );

    renderRecommendationsScreen();

    await userEvent.click(await screen.findByRole('button', { name: /back/i }));

    expect(navigateMock).toHaveBeenCalledWith(-1);
  });
});

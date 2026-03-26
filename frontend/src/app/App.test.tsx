import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';

import App from './App';
import { server } from '../test/server';

describe('App composition', () => {
  test('renders login when there is no authenticated user', () => {
    localStorage.removeItem('parrot_user');
    window.history.pushState({}, '', '/');

    render(<App />);

    expect(screen.getByText('Welcome, Traveler!')).toBeInTheDocument();
  });

  test('renders main routes when the user is authenticated', () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15551111111', name: 'Alice' })
    );
    window.history.pushState({}, '', '/');
    server.use(
      http.get('http://localhost:8000/notifications/:userId/count', () =>
        HttpResponse.json({ unread_count: 0 })
      )
    );

    render(<App />);

    expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import TopBar from './TopBar';

describe('TopBar', () => {
  test('shows the unread notifications badge when the count is greater than zero', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15551111111', name: 'Alice' })
    );
    server.use(
      http.get('http://localhost:8000/notifications/:userId/count', () =>
        HttpResponse.json({ unread_count: 5 })
      )
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <TopBar title="Trip" />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Trip')).toBeInTheDocument();
    expect(await screen.findByText('5')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /menu/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Local Recommendations')).not.toBeInTheDocument();
  });
});

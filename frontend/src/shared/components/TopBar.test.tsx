import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import TopBar from './TopBar';

describe('TopBar', () => {
  test('renders the provided title', () => {
    render(
      <MemoryRouter>
        <TopBar title="Trip" />
      </MemoryRouter>
    );

    expect(screen.getByText('Trip')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /menu/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Local Recommendations')).not.toBeInTheDocument();
  });
});

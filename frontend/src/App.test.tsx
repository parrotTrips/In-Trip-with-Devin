import { render, screen } from '@testing-library/react';

import App from './App';

test('renders login screen when the user is logged out', () => {
  localStorage.removeItem('parrot_user');

  render(<App />);

  expect(screen.getByText('Welcome, Traveler!')).toBeInTheDocument();
});

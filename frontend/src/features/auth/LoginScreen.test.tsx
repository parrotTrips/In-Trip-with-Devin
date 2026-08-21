import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import LoginScreen from './pages/LoginScreen';

describe('LoginScreen', () => {
  const supportedCountryCodes = [
    '+1', '+7', '+20', '+27', '+30', '+31', '+32', '+33', '+34', '+36',
    '+39', '+40', '+41', '+43', '+44', '+45', '+46', '+47', '+48', '+49',
    '+51', '+52', '+53', '+54', '+55', '+56', '+57', '+58', '+60', '+61',
    '+62', '+63', '+64', '+65', '+66', '+81', '+82', '+84', '+86', '+90',
    '+91', '+92', '+93', '+94', '+95', '+98', '+211', '+212', '+213',
    '+216', '+218', '+220', '+221', '+222', '+223', '+224', '+225',
    '+226', '+227', '+228', '+229', '+230', '+231', '+232', '+233',
    '+234', '+235', '+236', '+237', '+238', '+239', '+240', '+241',
    '+242', '+243', '+244', '+245', '+246', '+247', '+248', '+249',
    '+250', '+251', '+252', '+253', '+254', '+255', '+256', '+257',
    '+258', '+260', '+261', '+262', '+263', '+264', '+265', '+266',
    '+267', '+268', '+269', '+290', '+291', '+297', '+298', '+299',
    '+350', '+351', '+352', '+353', '+354', '+355', '+356', '+357',
    '+358', '+359', '+370', '+371', '+372', '+373', '+374', '+375',
    '+376', '+377', '+378', '+380', '+381', '+382', '+383', '+385',
    '+386', '+387', '+389', '+420', '+421', '+423', '+500', '+501',
    '+502', '+503', '+504', '+505', '+506', '+507', '+508', '+509',
    '+590', '+591', '+592', '+593', '+594', '+595', '+596', '+597',
    '+598', '+599', '+670', '+672', '+673', '+674', '+675', '+676',
    '+677', '+678', '+679', '+680', '+681', '+682', '+683', '+685',
    '+686', '+687', '+688', '+689', '+690', '+691', '+692', '+850',
    '+852', '+853', '+855', '+856', '+880', '+886', '+960', '+961',
    '+962', '+963', '+964', '+965', '+966', '+967', '+968', '+970',
    '+971', '+972', '+973', '+974', '+975', '+976', '+977', '+992',
    '+993', '+994', '+995', '+996', '+998',
  ];

  test('offers all supported country calling codes', () => {
    localStorage.removeItem('parrot_user');
    render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>
    );

    const selector = screen.getByRole('combobox');
    const options = Array.from(selector.querySelectorAll('option')).map(option => option.value);

    expect(options).toEqual(supportedCountryCodes);
  });

  test('submits the full phone number when requesting an OTP', async () => {
    let requestedPhone = '';

    server.use(
      http.post('http://localhost:8000/auth/request-otp', async ({ request }) => {
        const body = await request.json();
        requestedPhone = String((body as { phone: string }).phone);
        return HttpResponse.json({
          message: 'OTP generated (WhatsApp delivery failed, showing code for testing)',
          debug_code: '654321',
        });
      })
    );

    localStorage.removeItem('parrot_user');
    render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>
    );

    await userEvent.type(screen.getByPlaceholderText('Phone number'), '5551234567');
    await userEvent.click(screen.getByRole('button', { name: /send whatsapp code/i }));

    await waitFor(() => {
      expect(requestedPhone).toBe('+15551234567');
    });
    expect(screen.getByText('Verification Code')).toBeInTheDocument();
    expect(screen.getByText(/test code: 654321/i)).toBeInTheDocument();
  });

  test('submits a Portuguese phone number with the selected country code', async () => {
    let requestedPhone = '';

    server.use(
      http.post('http://localhost:8000/auth/request-otp', async ({ request }) => {
        const body = await request.json();
        requestedPhone = String((body as { phone: string }).phone);
        return HttpResponse.json({ message: 'OTP generated' });
      })
    );

    localStorage.removeItem('parrot_user');
    render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>
    );

    await userEvent.selectOptions(screen.getByRole('combobox'), '+351');
    await userEvent.type(screen.getByPlaceholderText('Phone number'), '935276544');
    await userEvent.click(screen.getByRole('button', { name: /send whatsapp code/i }));

    await waitFor(() => {
      expect(requestedPhone).toBe('+351935276544');
    });
  });
});

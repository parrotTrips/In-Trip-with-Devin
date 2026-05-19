import { request } from '../../../shared/api/client';

export async function requestOTP(phone: string) {
  return request<{ message: string; debug_code?: string }>('/auth/request-otp', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOTP(phone: string, code: string) {
  return request<{
    user_id: number;
    phone: string;
    name: string | null;
    message: string;
    access_token: string;
  }>(
    '/auth/verify-otp',
    { method: 'POST', body: JSON.stringify({ phone, code }) }
  );
}

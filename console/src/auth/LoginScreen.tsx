import { useState, type FormEvent } from 'react';

import { request } from '../api/client';
import { useAuth } from './auth-context';

interface VerifyResponse {
  user_id: string;
  phone: string;
  name: string | null;
  role: string;
  access_token: string;
}

export default function LoginScreen() {
  const { login, user } = useAuth();
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) return <p>Bem-vindo, {user.name ?? user.phone}</p>;

  const sendCode = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await request('/auth/request-otp', {
        method: 'POST',
        body: JSON.stringify({ phone: `+${phone}` }),
      });
      setCodeSent(true);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const verify = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      const res = await request<VerifyResponse>('/auth/verify-otp', {
        method: 'POST',
        body: JSON.stringify({ phone: `+${phone}`, code }),
      });
      // Checked before storing: a traveler with the right code gets a valid JWT,
      // but must not get into the console.
      if (res.role !== 'admin') {
        setError('Esta conta não tem acesso ao console.');
        return;
      }
      login({
        userId: res.user_id, phone: res.phone, name: res.name,
        token: res.access_token, role: res.role,
      });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="max-w-sm mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Parrot Trips — Console</h1>
      {!codeSent ? (
        <form onSubmit={sendCode} className="space-y-3">
          <label htmlFor="phone" className="block text-sm">Telefone</label>
          <input
            id="phone" value={phone} onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
            className="w-full border rounded px-3 py-2"
          />
          <button type="submit" className="w-full bg-black text-white rounded px-3 py-2">
            Enviar código
          </button>
        </form>
      ) : (
        <form onSubmit={verify} className="space-y-3">
          <label htmlFor="code" className="block text-sm">Código</label>
          <input
            id="code" value={code} onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
            className="w-full border rounded px-3 py-2"
          />
          <button type="submit" className="w-full bg-black text-white rounded px-3 py-2">
            Entrar
          </button>
        </form>
      )}
      {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
    </div>
  );
}

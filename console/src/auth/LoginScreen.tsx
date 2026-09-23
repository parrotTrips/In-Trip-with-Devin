import { useState, type FormEvent } from 'react';

import { request } from '../api/client';
import { useAuth } from './auth-context';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

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

  if (user) return <p className="p-6">Bem-vindo, {user.name ?? user.phone}</p>;

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
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center p-6">
      <img src="/parrot_icon.svg" alt="" className="mb-4 h-12 w-12" />
      <h1 className="mb-1 text-2xl font-bold tracking-tight">Parrot Trips — Console</h1>
      <p className="mb-6 text-sm text-muted-foreground">Entre para editar o conteúdo das viagens.</p>
      {!codeSent ? (
        <form onSubmit={sendCode} className="space-y-3">
          <Label htmlFor="phone">Telefone</Label>
          <Input
            id="phone" value={phone} placeholder="5511999999999"
            onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
          />
          <Button type="submit" className="w-full">Enviar código</Button>
        </form>
      ) : (
        <form onSubmit={verify} className="space-y-3">
          <Label htmlFor="code">Código</Label>
          <Input
            id="code" value={code} inputMode="numeric"
            onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
          />
          <Button type="submit" className="w-full">Entrar</Button>
        </form>
      )}
      {error && <Alert variant="destructive" className="mt-4">{error}</Alert>}
    </div>
  );
}

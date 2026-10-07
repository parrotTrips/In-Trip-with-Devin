import { GoogleLogin } from '@react-oauth/google';
import { useState } from 'react';

import { useAuth } from './auth-context';
import { Alert } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';

export default function LoginScreen() {
  const { config, login, principal } = useAuth();
  const [error, setError] = useState<string | null>(null);

  if (principal) return <p>Bem-vindo, {principal.email}</p>;

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-6">
      <Card className="w-full max-w-sm">
        <CardContent className="flex flex-col items-center p-8 text-center">
          <img src="/parrot_icon.svg" alt="" className="mb-4 h-12 w-12" />
          <h1 className="text-xl font-semibold tracking-tight">Parrot Trips — Console</h1>
          <p className="mb-6 mt-2 text-sm text-muted-foreground">
            Entre com sua conta corporativa @{config.allowedEmailDomain}.
          </p>
          <GoogleLogin
            hosted_domain={config.allowedEmailDomain}
            onSuccess={response => {
              setError(null);
              if (!response.credential || !login(response.credential)) {
                setError('A credencial Google recebida não é válida para este console.');
              }
            }}
            onError={() => setError('Não foi possível entrar com o Google.')}
          />
          {error && <Alert variant="destructive" className="mt-4 w-full">{error}</Alert>}
        </CardContent>
      </Card>
    </div>
  );
}

import { GoogleLogin } from '@react-oauth/google';
import { useState } from 'react';

import { useAuth } from './auth-context';

export default function LoginScreen() {
  const { config, login, principal } = useAuth();
  const [error, setError] = useState<string | null>(null);

  if (principal) return <p>Bem-vindo, {principal.email}</p>;

  return (
    <div className="max-w-sm mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Parrot Trips — Console</h1>
      <p className="text-sm text-gray-600 mb-4">
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
      {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
    </div>
  );
}

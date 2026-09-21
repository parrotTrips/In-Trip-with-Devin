# Content Console — App `console/` (Fatia A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o app `console/`, separado do app do viajante, onde um `admin` faz login por WhatsApp OTP e edita fases pré-trip, checklist e links de uma viagem, publicando quando quiser.

**Architecture:** Projeto Vite/React/TypeScript novo em `console/`, com deploy Netlify próprio. Consome a API `/console` já construída. Sem biblioteca de estado: `useState` e chamadas diretas, porque cada tela carrega uma árvore pequena e a salva inteira.

**Tech Stack:** Vite 6, React 18, TypeScript, react-router-dom 7, Tailwind 3, Vitest 2, Testing Library, MSW 2 — as mesmas versões do app do viajante.

**Spec:** `docs/superpowers/specs/2026-09-21-content-console-design.md`

## Global Constraints

- **Não alterar nada** em `frontend/`, `backend/` ou `google-apps-script/`. Este plano só cria arquivos dentro de `console/`, mais duas entradas no `Makefile` da raiz (Task 7).
- Token no `localStorage` sob a chave `parrot_console_user` — nunca `parrot_user`, que é do app do viajante.
- Quem não for `role === 'admin'` não entra: a tela de login recusa e não guarda o token.
- Link de pré-embarque, literal: `https://parrot-trips.netlify.app/profile?section=pre-departure`
- Comandos rodam de dentro de `console/`: `npm run test`, `npm run build`.
- TDD obrigatório: escrever o teste, vê-lo falhar pelo motivo certo, só então implementar.

---

### Task 1: Scaffold do projeto

**Files:**
- Create: `console/package.json`, `console/vite.config.ts`, `console/tsconfig.json`, `console/tsconfig.node.json`, `console/index.html`, `console/tailwind.config.js`, `console/postcss.config.js`, `console/vitest.config.ts`, `console/.gitignore`, `console/src/index.css`, `console/src/main.tsx`, `console/src/App.tsx`, `console/src/test/setup.ts`, `console/src/vite-env.d.ts`
- Test: `console/src/App.test.tsx`

**Interfaces:**
- Produces: `App` (default export de `src/App.tsx`), renderizado por `main.tsx`.

- [ ] **Step 1: Criar os arquivos de configuração**

`console/package.json`:

```json
{
  "name": "parrot-trips-console",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "preview": "vite preview"
  },
  "dependencies": {
    "lucide-react": "^0.364.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^7.13.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^14.6.1",
    "@types/node": "^25.3.2",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "jsdom": "^26.1.0",
    "msw": "^2.11.2",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "~5.6.2",
    "vite": "^6.0.1",
    "vitest": "^2.1.9"
  }
}
```

`console/vite.config.ts` — a config de teste fica em arquivo separado, como no app do viajante. Juntar as duas quebra o build: o Vitest 2 traz um Vite aninhado cujos tipos de plugin não batem com os do Vite 6, e `tsc -b` falha. Mantendo `vitest.config.ts` fora do `include` do tsconfig, o conflito não existe.

```typescript
import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
})
```

`console/vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
});
```

`console/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"],
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`console/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "composite": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

`console/index.html`:

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Parrot Trips — Console</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`console/tailwind.config.js`:

```javascript
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

`console/postcss.config.js`:

```javascript
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
```

`console/.gitignore`:

```
node_modules
dist
.env
.env.production
```

`console/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

`console/src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

`console/src/test/setup.ts`:

```typescript
import '@testing-library/jest-dom';
```

- [ ] **Step 2: Escrever o teste que falha**

`console/src/App.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';

import App from './App';

test('renders the console title', () => {
  render(<App />);
  expect(screen.getByText('Parrot Trips — Console')).toBeInTheDocument();
});
```

- [ ] **Step 3: Instalar dependências e ver o teste falhar**

Run: `cd console && npm install && npm run test`
Expected: FAIL — `Failed to resolve import "./App"`, porque `App.tsx` ainda não existe.

- [ ] **Step 4: Implementar o mínimo**

`console/src/App.tsx`:

```typescript
export default function App() {
  return <h1>Parrot Trips — Console</h1>;
}
```

`console/src/main.tsx`:

```typescript
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 5: Verificar teste e build**

Run: `cd console && npm run test && npm run build`
Expected: 1 teste passa e o build gera `dist/` sem erro de TypeScript.

- [ ] **Step 6: Commit**

```bash
git add console/
git commit -m "feat(console): scaffold the standalone console app"
```

---

### Task 2: Cliente HTTP, autenticação e guard de admin

**Files:**
- Create: `console/src/api/client.ts`, `console/src/auth/auth-context.ts`, `console/src/auth/AuthProvider.tsx`, `console/src/auth/LoginScreen.tsx`
- Modify: `console/src/App.tsx`
- Test: `console/src/auth/LoginScreen.test.tsx`

**Interfaces:**
- Produces:
  - `request<T>(path: string, options?: RequestInit): Promise<T>` — lê o token de `parrot_console_user`
  - `AuthUser = { userId: string; phone: string; name: string | null; token: string; role: string }`
  - `useAuth(): { user: AuthUser | null; login(u: AuthUser): void; logout(): void; isLoggedIn: boolean }`
  - `LoginScreen` — telefone, código, e recusa de não-admin

- [ ] **Step 1: Escrever os testes que falham**

`console/src/auth/LoginScreen.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { AuthProvider } from './AuthProvider';
import LoginScreen from './LoginScreen';

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

afterEach(() => {
  localStorage.clear();
});

function mockFetchSequence(responses: object[]) {
  const fetchMock = vi.fn();
  responses.forEach(body => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => body,
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

test('an admin logging in is stored', async () => {
  mockFetchSequence([
    { message: 'sent' },
    {
      user_id: 'u1', phone: '+5511999999999', name: 'Admin',
      role: 'admin', message: 'ok', access_token: 'tok',
    },
  ]);

  render(<AuthProvider><LoginScreen /></AuthProvider>);

  await userEvent.type(screen.getByLabelText('Telefone'), '5511999999999');
  await userEvent.click(screen.getByRole('button', { name: 'Enviar código' }));
  await userEvent.type(await screen.findByLabelText('Código'), '123456');
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));

  await screen.findByText(/Bem-vindo/);
  expect(JSON.parse(localStorage.getItem('parrot_console_user')!).role).toBe('admin');
});

test('a non-admin is refused and nothing is stored', async () => {
  mockFetchSequence([
    { message: 'sent' },
    {
      user_id: 'u2', phone: '+5511888888888', name: 'Viajante',
      role: 'traveler', message: 'ok', access_token: 'tok',
    },
  ]);

  render(<AuthProvider><LoginScreen /></AuthProvider>);

  await userEvent.type(screen.getByLabelText('Telefone'), '5511888888888');
  await userEvent.click(screen.getByRole('button', { name: 'Enviar código' }));
  await userEvent.type(await screen.findByLabelText('Código'), '123456');
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));

  expect(await screen.findByText('Esta conta não tem acesso ao console.')).toBeInTheDocument();
  expect(localStorage.getItem('parrot_console_user')).toBeNull();
});
```

- [ ] **Step 2: Rodar e verificar que falham**

Run: `cd console && npm run test`
Expected: FAIL — `Failed to resolve import "./AuthProvider"`.

- [ ] **Step 3: Implementar cliente e contexto**

`console/src/api/client.ts`:

```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const STORAGE_KEY = 'parrot_console_user';

function getToken(): string | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    return (JSON.parse(stored) as { token?: string }).token ?? null;
  } catch {
    return null;
  }
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Request failed');
  }
  return response.json();
}
```

`console/src/auth/auth-context.ts`:

```typescript
import { createContext, useContext } from 'react';

export interface AuthUser {
  userId: string;
  phone: string;
  name: string | null;
  token: string;
  role: string;
}

export interface AuthContextType {
  user: AuthUser | null;
  login: (user: AuthUser) => void;
  logout: () => void;
  isLoggedIn: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => {},
  logout: () => {},
  isLoggedIn: false,
});

export function useAuth() {
  return useContext(AuthContext);
}
```

`console/src/auth/AuthProvider.tsx`:

```typescript
import { useState, type ReactNode } from 'react';

import { STORAGE_KEY } from '../api/client';
import { AuthContext, type AuthUser } from './auth-context';

function getStoredUser(): AuthUser | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? (JSON.parse(stored) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(getStoredUser);

  const login = (newUser: AuthUser) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newUser));
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}
```

- [ ] **Step 4: Implementar a tela de login**

O papel é checado **antes** de guardar o token: um viajante que digitar o código certo recebe um JWT válido, mas não entra no console.

`console/src/auth/LoginScreen.tsx`:

```typescript
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
```

- [ ] **Step 5: Ligar no App**

`console/src/App.tsx` passa a ser:

```typescript
import { AuthProvider } from './auth/AuthProvider';
import LoginScreen from './auth/LoginScreen';

export default function App() {
  return (
    <AuthProvider>
      <LoginScreen />
    </AuthProvider>
  );
}
```

`App.test.tsx` continua válido: o `h1` da tela de login tem o mesmo texto.

- [ ] **Step 6: Rodar os testes**

Run: `cd console && npm run test`
Expected: PASS (3 testes)

- [ ] **Step 7: Commit**

```bash
git add console/
git commit -m "feat(console): OTP login with admin-only access"
```

---

### Task 3: Tela de viagens e link de pré-embarque

**Files:**
- Create: `console/src/api/console-api.ts`, `console/src/pages/TripsScreen.tsx`
- Modify: `console/src/App.tsx`
- Test: `console/src/pages/TripsScreen.test.tsx`

**Interfaces:**
- Produces:
  - `Trip = { trip_uuid: string; title: string; start_date: string | null; end_date: string | null }`
  - `listTrips(): Promise<{ trips: Trip[] }>`
  - `PRE_DEPARTURE_LINK` — a constante literal do link
  - `TripsScreen`

- [ ] **Step 1: Escrever o teste que falha**

```typescript
// console/src/pages/TripsScreen.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import TripsScreen from './TripsScreen';

beforeEach(() => {
  vi.restoreAllMocks();
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      trips: [{
        trip_uuid: 'T1', title: 'Viagem Um',
        start_date: '2027-07-01', end_date: '2027-07-10',
      }],
    }),
  }));
});

test('lists trips returned by the API', async () => {
  render(<MemoryRouter><TripsScreen /></MemoryRouter>);
  expect(await screen.findByText('Viagem Um')).toBeInTheDocument();
});

test('copies the pre-departure link to the clipboard', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } });

  render(<MemoryRouter><TripsScreen /></MemoryRouter>);
  await screen.findByText('Viagem Um');
  await userEvent.click(screen.getByRole('button', { name: 'Copiar link de pré-embarque' }));

  expect(writeText).toHaveBeenCalledWith(
    'https://parrot-trips.netlify.app/profile?section=pre-departure'
  );
});
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `cd console && npm run test`
Expected: FAIL — `Failed to resolve import "./TripsScreen"`.

- [ ] **Step 3: Implementar a API**

`console/src/api/console-api.ts`:

```typescript
import { request } from './client';

export const PRE_DEPARTURE_LINK =
  'https://parrot-trips.netlify.app/profile?section=pre-departure';

export interface Trip {
  trip_uuid: string;
  title: string;
  start_date: string | null;
  end_date: string | null;
}

export function listTrips() {
  return request<{ trips: Trip[] }>('/console/trips');
}
```

- [ ] **Step 4: Implementar a tela**

`console/src/pages/TripsScreen.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { listTrips, PRE_DEPARTURE_LINK, type Trip } from '../api/console-api';

export default function TripsScreen() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    listTrips()
      .then(data => setTrips(data.trips))
      .catch(err => setError((err as Error).message));
  }, []);

  const copyLink = async () => {
    await navigator.clipboard.writeText(PRE_DEPARTURE_LINK);
    setCopied(true);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Viagens</h1>
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
      <ul className="space-y-2 mb-6">
        {trips.map(trip => (
          <li key={trip.trip_uuid} className="border rounded p-3">
            <Link to={`/trips/${trip.trip_uuid}/phases`} className="font-medium underline">
              {trip.title}
            </Link>
            <p className="text-sm text-gray-600">
              {trip.start_date} — {trip.end_date}
            </p>
          </li>
        ))}
      </ul>
      <button onClick={copyLink} className="border rounded px-3 py-2">
        Copiar link de pré-embarque
      </button>
      {copied && <span className="ml-2 text-sm text-green-700">Copiado</span>}
    </div>
  );
}
```

- [ ] **Step 5: Ligar o roteador no App**

```typescript
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AuthProvider } from './auth/AuthProvider';
import { useAuth } from './auth/auth-context';
import LoginScreen from './auth/LoginScreen';
import TripsScreen from './pages/TripsScreen';

function Routed() {
  const { isLoggedIn } = useAuth();
  if (!isLoggedIn) return <LoginScreen />;
  return (
    <Routes>
      <Route path="/" element={<TripsScreen />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routed />
      </BrowserRouter>
    </AuthProvider>
  );
}
```

- [ ] **Step 6: Rodar os testes**

Run: `cd console && npm run test`
Expected: PASS (5 testes)

- [ ] **Step 7: Commit**

```bash
git add console/
git commit -m "feat(console): trips screen with pre-departure link button"
```

---

### Task 4: Tela de fases — listar, criar, publicar, excluir

**Files:**
- Modify: `console/src/api/console-api.ts`, `console/src/App.tsx`
- Create: `console/src/pages/PhasesScreen.tsx`
- Test: `console/src/pages/PhasesScreen.test.tsx`

**Interfaces:**
- Produces:
  - `ChecklistItem = { id: string; label: string; is_required: boolean; sort_order: number }`
  - `PhaseLink = { id: string; label: string; url: string; sort_order: number }`
  - `Phase = { id: string; title: string; subtitle: string | null; icon: string | null; short_description: string; detailed_description: string | null; sort_order: number; is_visible: boolean; checklist: ChecklistItem[]; links: PhaseLink[] }`
  - `getPhases(tripUuid)`, `createPhase(tripUuid, body)`, `publishPhase(id)`, `unpublishPhase(id)`, `deletePhase(id)`
  - `PhasesScreen`

- [ ] **Step 1: Escrever o teste que falha**

```typescript
// console/src/pages/PhasesScreen.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import PhasesScreen from './PhasesScreen';

function phase(overrides = {}) {
  return {
    id: 'p1', title: 'Documentos', subtitle: null, icon: null,
    short_description: '', detailed_description: null,
    sort_order: 0, is_visible: false, checklist: [], links: [],
    ...overrides,
  };
}

function renderAt(tripUuid: string) {
  return render(
    <MemoryRouter initialEntries={[`/trips/${tripUuid}/phases`]}>
      <Routes>
        <Route path="/trips/:tripUuid/phases" element={<PhasesScreen />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.restoreAllMocks());

test('shows a draft phase as draft', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, json: async () => ({ phases: [phase()] }),
  }));

  renderAt('T1');

  expect(await screen.findByText('Documentos')).toBeInTheDocument();
  expect(screen.getByText('Rascunho')).toBeInTheDocument();
});

test('publishing calls the API and shows the phase as published', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase()] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'p1', is_visible: true }) })
    .mockResolvedValueOnce({
      ok: true, json: async () => ({ phases: [phase({ is_visible: true })] }),
    });
  vi.stubGlobal('fetch', fetchMock);

  renderAt('T1');
  await screen.findByText('Documentos');
  await userEvent.click(screen.getByRole('button', { name: 'Publicar' }));

  expect(await screen.findByText('Publicada')).toBeInTheDocument();
  expect(fetchMock.mock.calls[1][0]).toContain('/console/phases/p1/publish');
});
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `cd console && npm run test`
Expected: FAIL — `Failed to resolve import "./PhasesScreen"`.

- [ ] **Step 3: Estender a API**

Acrescentar a `console/src/api/console-api.ts`:

```typescript
export interface ChecklistItem {
  id: string;
  label: string;
  is_required: boolean;
  sort_order: number;
}

export interface PhaseLink {
  id: string;
  label: string;
  url: string;
  sort_order: number;
}

export interface Phase {
  id: string;
  title: string;
  subtitle: string | null;
  icon: string | null;
  short_description: string;
  detailed_description: string | null;
  sort_order: number;
  is_visible: boolean;
  checklist: ChecklistItem[];
  links: PhaseLink[];
}

export function getPhases(tripUuid: string) {
  return request<{ phases: Phase[] }>(`/console/trips/${tripUuid}/phases`);
}

export function createPhase(tripUuid: string, body: { title: string; short_description: string }) {
  return request<{ id: string; is_visible: boolean }>(
    `/console/trips/${tripUuid}/phases`,
    { method: 'POST', body: JSON.stringify(body) }
  );
}

export function publishPhase(phaseId: string) {
  return request<{ id: string; is_visible: boolean }>(
    `/console/phases/${phaseId}/publish`, { method: 'POST' }
  );
}

export function unpublishPhase(phaseId: string) {
  return request<{ id: string; is_visible: boolean }>(
    `/console/phases/${phaseId}/unpublish`, { method: 'POST' }
  );
}

export function deletePhase(phaseId: string) {
  return request<{ id: string; deleted: boolean }>(
    `/console/phases/${phaseId}`, { method: 'DELETE' }
  );
}
```

- [ ] **Step 4: Implementar a tela**

`console/src/pages/PhasesScreen.tsx`:

```typescript
import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  createPhase, deletePhase, getPhases, publishPhase, unpublishPhase, type Phase,
} from '../api/console-api';

export default function PhasesScreen() {
  const { tripUuid = '' } = useParams();
  const [phases, setPhases] = useState<Phase[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setPhases((await getPhases(tripUuid)).phases);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [tripUuid]);

  useEffect(() => { void reload(); }, [reload]);

  const act = async (action: () => Promise<unknown>) => {
    setError(null);
    try {
      await action();
      await reload();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Link to="/" className="text-sm underline">← Viagens</Link>
      <h1 className="text-xl font-bold my-4">Fases</h1>
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      <ul className="space-y-2 mb-6">
        {phases.map(phase => (
          <li key={phase.id} className="border rounded p-3 flex items-center gap-3">
            <div className="flex-1">
              <Link to={`/trips/${tripUuid}/phases/${phase.id}`} className="font-medium underline">
                {phase.title}
              </Link>
              <p className="text-sm text-gray-600">
                {phase.checklist.length} itens · {phase.links.length} links
              </p>
            </div>
            <span className={phase.is_visible ? 'text-green-700 text-sm' : 'text-amber-700 text-sm'}>
              {phase.is_visible ? 'Publicada' : 'Rascunho'}
            </span>
            <button
              className="border rounded px-2 py-1 text-sm"
              onClick={() => act(() =>
                phase.is_visible ? unpublishPhase(phase.id) : publishPhase(phase.id)
              )}
            >
              {phase.is_visible ? 'Despublicar' : 'Publicar'}
            </button>
            <button
              className="border rounded px-2 py-1 text-sm text-red-700"
              onClick={() => act(() => deletePhase(phase.id))}
            >
              Excluir
            </button>
          </li>
        ))}
      </ul>

      <button
        className="border rounded px-3 py-2"
        onClick={() => act(() =>
          createPhase(tripUuid, { title: 'Nova fase', short_description: '' })
        )}
      >
        Nova fase
      </button>
    </div>
  );
}
```

- [ ] **Step 5: Registrar a rota no App**

Acrescentar dentro de `<Routes>`:

```typescript
<Route path="/trips/:tripUuid/phases" element={<PhasesScreen />} />
```

- [ ] **Step 6: Rodar os testes**

Run: `cd console && npm run test`
Expected: PASS (7 testes)

- [ ] **Step 7: Commit**

```bash
git add console/
git commit -m "feat(console): phases screen with draft state and publishing"
```

---

### Task 5: Editor de fase — campos, checklist e links

**Files:**
- Modify: `console/src/api/console-api.ts`, `console/src/App.tsx`
- Create: `console/src/lib/move-up.ts`, `console/src/pages/PhaseEditor.tsx`
- Test: `console/src/pages/PhaseEditor.test.tsx`

`moveUp` vive em `lib/` porque a Task 6 reusa a mesma função na tela de fases.

```typescript
// console/src/lib/move-up.ts
export function moveUp<T>(list: T[], index: number): T[] {
  if (index <= 0) return list;
  const next = [...list];
  [next[index - 1], next[index]] = [next[index], next[index - 1]];
  return next;
}
```

**Interfaces:**
- Produces:
  - `updatePhase(phaseId, body)`, `replaceChecklist(phaseId, items)`, `replaceLinks(phaseId, links)`
  - `PhaseEditor`

O editor carrega a árvore da viagem, encontra a fase pela rota e salva em três chamadas: os campos por `PATCH`, o checklist e os links por `PUT` de lista inteira. Mover um item para cima ou para baixo é reordenar o array local — a posição vira `sort_order` no servidor.

- [ ] **Step 1: Escrever o teste que falha**

```typescript
// console/src/pages/PhaseEditor.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import PhaseEditor from './PhaseEditor';

const phase = {
  id: 'p1', title: 'Documentos', subtitle: null, icon: null,
  short_description: 'curta', detailed_description: null,
  sort_order: 0, is_visible: false,
  checklist: [
    { id: 'c1', label: 'Passaporte', is_required: true, sort_order: 0 },
    { id: 'c2', label: 'Visto', is_required: false, sort_order: 1 },
  ],
  links: [],
};

function renderEditor() {
  return render(
    <MemoryRouter initialEntries={['/trips/T1/phases/p1']}>
      <Routes>
        <Route path="/trips/:tripUuid/phases/:phaseId" element={<PhaseEditor />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.restoreAllMocks());

test('saving sends title and checklist in screen order', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase] }) })
    .mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
  vi.stubGlobal('fetch', fetchMock);

  renderEditor();

  const title = await screen.findByLabelText('Título');
  await userEvent.clear(title);
  await userEvent.type(title, 'Novo título');

  // sobe "Visto" para a primeira posição
  await userEvent.click(screen.getAllByRole('button', { name: 'Subir' })[1]);
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  await screen.findByText('Salvo');

  const patchCall = fetchMock.mock.calls.find(c => c[1]?.method === 'PATCH');
  expect(JSON.parse(patchCall![1].body).title).toBe('Novo título');

  const checklistCall = fetchMock.mock.calls.find(c => String(c[0]).endsWith('/checklist'));
  expect(JSON.parse(checklistCall![1].body).items.map((i: { label: string }) => i.label))
    .toEqual(['Visto', 'Passaporte']);
});
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `cd console && npm run test`
Expected: FAIL — `Failed to resolve import "./PhaseEditor"`.

- [ ] **Step 3: Estender a API**

```typescript
export function updatePhase(phaseId: string, body: Partial<Pick<Phase,
  'title' | 'subtitle' | 'icon' | 'short_description' | 'detailed_description'>>) {
  return request<{ id: string; updated: boolean }>(
    `/console/phases/${phaseId}`, { method: 'PATCH', body: JSON.stringify(body) }
  );
}

export function replaceChecklist(
  phaseId: string, items: { label: string; is_required: boolean }[]
) {
  return request<{ count: number }>(
    `/console/phases/${phaseId}/checklist`,
    { method: 'PUT', body: JSON.stringify({ items }) }
  );
}

export function replaceLinks(phaseId: string, links: { label: string; url: string }[]) {
  return request<{ count: number }>(
    `/console/phases/${phaseId}/links`,
    { method: 'PUT', body: JSON.stringify({ links }) }
  );
}
```

- [ ] **Step 4: Implementar o editor**

`console/src/pages/PhaseEditor.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  getPhases, replaceChecklist, replaceLinks, updatePhase,
  type ChecklistItem, type Phase, type PhaseLink,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';

export default function PhaseEditor() {
  const { tripUuid = '', phaseId = '' } = useParams();
  const [phase, setPhase] = useState<Phase | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [links, setLinks] = useState<PhaseLink[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPhases(tripUuid)
      .then(data => {
        const found = data.phases.find(p => p.id === phaseId) ?? null;
        setPhase(found);
        setChecklist(found?.checklist ?? []);
        setLinks(found?.links ?? []);
      })
      .catch(err => setError((err as Error).message));
  }, [tripUuid, phaseId]);

  if (error) return <p className="p-6 text-red-600">{error}</p>;
  if (!phase) return <p className="p-6">Carregando…</p>;

  const save = async () => {
    setStatus(null);
    setError(null);
    try {
      await updatePhase(phaseId, {
        title: phase.title,
        subtitle: phase.subtitle,
        icon: phase.icon,
        short_description: phase.short_description,
        detailed_description: phase.detailed_description,
      });
      await replaceChecklist(
        phaseId, checklist.map(i => ({ label: i.label, is_required: i.is_required }))
      );
      await replaceLinks(phaseId, links.map(l => ({ label: l.label, url: l.url })));
      setStatus('Salvo');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Link to={`/trips/${tripUuid}/phases`} className="text-sm underline">← Fases</Link>
      <h1 className="text-xl font-bold my-4">Editar fase</h1>

      <label htmlFor="title" className="block text-sm">Título</label>
      <input
        id="title" value={phase.title}
        onChange={e => setPhase({ ...phase, title: e.target.value })}
        className="w-full border rounded px-3 py-2 mb-3"
      />

      <label htmlFor="short" className="block text-sm">Descrição curta</label>
      <input
        id="short" value={phase.short_description}
        onChange={e => setPhase({ ...phase, short_description: e.target.value })}
        className="w-full border rounded px-3 py-2 mb-3"
      />

      <label htmlFor="detailed" className="block text-sm">Descrição completa</label>
      <textarea
        id="detailed" value={phase.detailed_description ?? ''}
        onChange={e => setPhase({ ...phase, detailed_description: e.target.value })}
        className="w-full border rounded px-3 py-2 mb-6"
      />

      <h2 className="font-bold mb-2">Checklist</h2>
      <ul className="space-y-2 mb-3">
        {checklist.map((item, index) => (
          <li key={item.id} className="flex items-center gap-2">
            <input
              aria-label={`Item ${index + 1}`} value={item.label}
              onChange={e => setChecklist(checklist.map(
                (i, idx) => idx === index ? { ...i, label: e.target.value } : i
              ))}
              className="flex-1 border rounded px-2 py-1"
            />
            <button className="border rounded px-2 py-1 text-sm"
                    onClick={() => setChecklist(moveUp(checklist, index))}>
              Subir
            </button>
            <button className="border rounded px-2 py-1 text-sm text-red-700"
                    onClick={() => setChecklist(checklist.filter((_, idx) => idx !== index))}>
              Remover
            </button>
          </li>
        ))}
      </ul>
      <button
        className="border rounded px-3 py-1 text-sm mb-6"
        onClick={() => setChecklist([
          ...checklist,
          { id: `new-${checklist.length}`, label: '', is_required: false, sort_order: checklist.length },
        ])}
      >
        Adicionar item
      </button>

      <h2 className="font-bold mb-2">Links</h2>
      <ul className="space-y-2 mb-3">
        {links.map((link, index) => (
          <li key={link.id} className="flex items-center gap-2">
            <input
              aria-label={`Link ${index + 1} rótulo`} value={link.label}
              onChange={e => setLinks(links.map(
                (l, idx) => idx === index ? { ...l, label: e.target.value } : l
              ))}
              className="flex-1 border rounded px-2 py-1"
            />
            <input
              aria-label={`Link ${index + 1} url`} value={link.url}
              onChange={e => setLinks(links.map(
                (l, idx) => idx === index ? { ...l, url: e.target.value } : l
              ))}
              className="flex-1 border rounded px-2 py-1"
            />
            <button className="border rounded px-2 py-1 text-sm text-red-700"
                    onClick={() => setLinks(links.filter((_, idx) => idx !== index))}>
              Remover
            </button>
          </li>
        ))}
      </ul>
      <button
        className="border rounded px-3 py-1 text-sm mb-6"
        onClick={() => setLinks([
          ...links,
          { id: `new-${links.length}`, label: '', url: '', sort_order: links.length },
        ])}
      >
        Adicionar link
      </button>

      <div className="flex items-center gap-3">
        <button onClick={save} className="bg-black text-white rounded px-4 py-2">Salvar</button>
        {status && <span className="text-green-700 text-sm">{status}</span>}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Registrar a rota**

```typescript
<Route path="/trips/:tripUuid/phases/:phaseId" element={<PhaseEditor />} />
```

E, em `PhasesScreen.tsx`, o link da fase passa a apontar para a rota com a viagem:

```typescript
<Link to={`/trips/${tripUuid}/phases/${phase.id}`} className="font-medium underline">
```

- [ ] **Step 6: Rodar os testes**

Run: `cd console && npm run test`
Expected: PASS (8 testes)

- [ ] **Step 7: Commit**

```bash
git add console/
git commit -m "feat(console): phase editor with checklist and links"
```

---

### Task 6: Reordenar fases

**Files:**
- Modify: `console/src/api/console-api.ts`, `console/src/pages/PhasesScreen.tsx`
- Test: `console/src/pages/PhasesScreen.test.tsx`

**Interfaces:**
- Produces: `reorderPhases(tripUuid, phaseIds: string[])`

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `PhasesScreen.test.tsx`:

```typescript
test('moving a phase up sends the new order', async () => {
  const two = [phase(), phase({ id: 'p2', title: 'Bagagem', sort_order: 1 })];
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: two }) })
    .mockResolvedValue({ ok: true, json: async () => ({ count: 2 }) });
  vi.stubGlobal('fetch', fetchMock);

  renderAt('T1');
  await screen.findByText('Bagagem');
  await userEvent.click(screen.getAllByRole('button', { name: 'Subir' })[1]);

  const orderCall = fetchMock.mock.calls.find(c => String(c[0]).endsWith('/phases/order'));
  expect(JSON.parse(orderCall![1].body).phase_ids).toEqual(['p2', 'p1']);
});
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `cd console && npm run test`
Expected: FAIL — não existe botão com o nome "Subir" nesta tela.

- [ ] **Step 3: Estender a API**

```typescript
export function reorderPhases(tripUuid: string, phaseIds: string[]) {
  return request<{ count: number }>(
    `/console/trips/${tripUuid}/phases/order`,
    { method: 'PUT', body: JSON.stringify({ phase_ids: phaseIds }) }
  );
}
```

- [ ] **Step 4: Adicionar o botão na tela de fases**

No topo do arquivo, incluir `reorderPhases` nos imports de API e `moveUp`:

```typescript
import { moveUp } from '../lib/move-up';
```

E, dentro do `<li>`, antes do botão de publicar:

```typescript
<button
  className="border rounded px-2 py-1 text-sm"
  onClick={() => {
    const reordered = moveUp(phases, index);
    setPhases(reordered);
    void act(() => reorderPhases(tripUuid, reordered.map(p => p.id)));
  }}
>
  Subir
</button>
```

Para ter o `index`, o `map` passa a ser `phases.map((phase, index) => ...)`.

- [ ] **Step 5: Rodar os testes**

Run: `cd console && npm run test`
Expected: PASS (9 testes)

- [ ] **Step 6: Commit**

```bash
git add console/
git commit -m "feat(console): reorder phases from the phases screen"
```

---

### Task 7: Configuração de deploy

**Files:**
- Create: `console/netlify.toml`, `console/.env.example`
- Modify: `Makefile` (raiz)

**Interfaces:**
- Produces: alvos `console-build` e `console-deploy` no Makefile.

- [ ] **Step 1: Criar o netlify.toml**

O fallback de SPA é obrigatório: sem ele, recarregar a página em `/trips/T1/phases` devolve 404.

`console/netlify.toml`:

```toml
[build]
  publish = "dist"
  command = "npm run build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

`console/.env.example`:

```
VITE_API_URL=https://parrot-trips-backend-428743191336.southamerica-east1.run.app
```

- [ ] **Step 2: Acrescentar os alvos ao Makefile da raiz**

No fim do arquivo:

```makefile
.PHONY: console-build
console-build:
	@echo "Building console..."
	cd console && npm run build

.PHONY: console-deploy
console-deploy: console-build
	@echo "Deploying console to Netlify..."
	cd console && netlify deploy --prod --dir=dist --site=$(CONSOLE_NETLIFY_SITE)
```

- [ ] **Step 3: Verificar o build**

Run: `cd console && npm run build`
Expected: `dist/` gerado, sem erro de TypeScript.

- [ ] **Step 4: Commit**

```bash
git add console/netlify.toml console/.env.example Makefile
git commit -m "chore(console): netlify config and make targets"
```

---

## Depois deste plano

A fatia A fica completa de ponta a ponta. Antes do primeiro uso real:

1. `make deploy-backend` — a API `/console` ainda não está no ar, e o fix dos scan events também não.
2. Criar o site Netlify do console e definir `CONSOLE_NETLIFY_SITE`.
3. Promover o primeiro admin, uma vez:

```sql
UPDATE users SET role = 'admin' WHERE phone = '<telefone>';
```

Depois disso, seguem as fatias B (Roteiro), C (Informações), D (Staff) e E (Operação), cada uma com seu spec e plano.

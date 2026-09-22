# Console de Conteúdo — SSO e Estabilização da Fatia A

**Data:** 2026-09-22
**Status:** Aprovado

## Objetivo

Colocar a fatia A do console de conteúdo em condição segura de produção. O trabalho substitui o login por WhatsApp por Google Workspace SSO, protege alterações destrutivas, torna o salvamento atômico e estabelece um processo verificável de deploy e rollback.

As fatias B–E, auditoria completa e histórico de versões permanecem fora deste escopo.

## Contexto atual

O repositório já contém:

- um app React independente em `console/`;
- rotas FastAPI em `/console/*`;
- CRUD de fases pré-trip, checklist e links;
- autenticação atual por JWT interno, emitido após OTP no WhatsApp;
- autorização por `users.role = 'admin'` em cada handler;
- deploy independente do console no Netlify.

O console ainda não foi publicado. O backend e o app do viajante já usam um middleware JWT global, que deve continuar funcionando sem alteração de comportamento.

## Decisões

| Tema | Decisão |
|---|---|
| Provedor de identidade | Google Identity Services |
| Fluxo | Google ID token stateless, enviado como Bearer |
| Domínio autorizado | `parrottrips.com` |
| Quem acessa | Toda conta ativa do Workspace que satisfaça os claims exigidos |
| Allowlist e papéis | Não haverá; todos têm acesso completo |
| Sessão no browser | `sessionStorage`, nunca `localStorage` |
| Sessão no backend | Nenhuma |
| Client secret, callback e refresh token | Não utilizados |
| Proteção da API | Dependência aplicada ao router `/console` inteiro |
| Bypass local | Somente com guardas explícitas no frontend e backend |
| Banco de usuários | Não participa da autenticação do console |

## Alternativas consideradas

### Dependência Google no router `/console` — escolhida

O middleware JWT legado deixa `/console` seguir até o router, e o router aplica `Depends(require_console_access)` a todas as rotas. Isso isola os dois sistemas de autenticação e reduz o risco de regressão no app do viajante.

### Middleware global com dois tipos de JWT

Foi descartado porque mistura tokens internos e Google no mesmo componente, aumentando a complexidade e a chance de aceitar um token no contexto errado.

### Backend separado para o console

Foi descartado porque duplicaria deploy, configuração e acesso ao banco sem benefício proporcional nesta fase.

## Arquitetura de autenticação

```text
Conta Google Workspace autenticada
        ↓
Google Identity Services
        ↓
Google ID token JWT
        ↓
sessionStorage do console
        ↓
Authorization: Bearer <ID token>
        ↓
/console/* → require_console_access
        ↓
assinatura, audience, issuer, expiração e claims corporativos
        ↓
serviços atuais do console → banco de dados
```

O router `/console` será excluído apenas da validação JWT interna. Isso não o torna público: a dependência Google será declarada no próprio `APIRouter`, evitando que uma rota nova seja criada sem autenticação por esquecimento.

As rotas de viajantes e staff continuarão usando o JWT interno. `/health` continuará público. `/admin` continuará separado por compatibilidade com o Apps Script.

## Frontend

O `console/` usará `@react-oauth/google`:

- `GoogleOAuthProvider` recebe `VITE_GOOGLE_CLIENT_ID`;
- `GoogleLogin` recebe `hosted_domain="parrottrips.com"` apenas como dica de UX;
- a credencial será armazenada em `sessionStorage` sob uma chave exclusiva;
- a restauração decodifica o payload somente para UX e verifica formato, `sub`, `email`, domínio e `exp`;
- nenhuma decisão de segurança depende dessa decodificação local;
- todas as chamadas protegidas recebem o Bearer em um cliente HTTP central;
- um 401 remove somente a credencial usada naquela requisição, impedindo que uma resposta atrasada apague uma sessão mais nova;
- 403 e 503 não encerram automaticamente uma sessão válida;
- logout limpa a credencial e desativa o auto-select do Google.

Fora de desenvolvimento, a aplicação bloqueará a inicialização se a URL da API, o Client ID ou o domínio estiverem ausentes ou inválidos.

## Backend

Uma dependência `require_console_access` validará o ID token com `google.oauth2.id_token.verify_oauth2_token` e retornará um principal com `uid` e `email`.

A validação exige:

- assinatura válida do Google;
- issuer aceito pela biblioteca oficial;
- token não expirado;
- audience exatamente igual a `GOOGLE_OAUTH_CLIENT_ID`;
- `email_verified is True`;
- `sub` presente e não vazio;
- `email` pertencente exatamente a `@parrottrips.com`;
- claim `hd` exatamente igual a `parrottrips.com`.

Semântica de resposta:

| Status | Situação |
|---|---|
| 401 | Bearer ausente, malformado, vencido, assinatura/issuer/audience inválidos |
| 403 | Token Google válido, mas claims corporativos não autorizados |
| 503 | Configuração obrigatória ausente |
| 500 | Falha inesperada e sanitizada durante a verificação |

O token bruto não aparecerá em logs nem mensagens de erro. A verificação síncrona será executada fora do event loop, com transporte HTTP reutilizável, cache pequeno de certificados e timeout explícito.

## Bypass local

O backend só permite bypass quando as duas condições forem verdadeiras:

```env
APP_ENV=development
ENABLE_CONSOLE_LOCAL=true
```

O frontend também exige simultaneamente:

```env
VITE_ENABLE_CONSOLE_LOCAL=true
```

e `import.meta.env.DEV`. Variáveis acidentalmente ligadas em produção não liberam acesso.

## Segurança de edição

- Fases publicadas ficam somente leitura.
- Para editar, é necessário despublicar primeiro.
- Para excluir, é necessário despublicar e confirmar digitando o título da fase.
- O backend recusa a exclusão de uma fase publicada, independentemente da interface.
- O salvamento de fase, checklist e links será uma única transação do banco.
- Campos obrigatórios não aceitam conteúdo vazio.
- URLs precisam usar `http` ou `https` e ser válidas.
- `ends_at` não pode ser anterior a `starts_at`.
- Ações bloqueiam seus controles enquanto estão em andamento e mostram resultado claro.
- Um aviso persistente informa que o import legado da planilha pode sobrescrever dados do console.

Histórico de versões e auditoria persistente ficam fora deste escopo. O principal Google será devolvido pela dependência para permitir auditoria futura.

## API atômica

O editor deixará de executar três requests independentes. Um único endpoint atualizará fase, checklist e links dentro de uma transação. Qualquer falha fará rollback integral.

As rotas separadas existentes podem permanecer temporariamente para compatibilidade interna, mas o console deixará de utilizá-las. A remoção dessas rotas não é necessária nesta entrega.

## CORS e documentação

O backend receberá uma lista explícita de origens permitidas. Ela deverá preservar as origens do app do viajante e adicionar a origem do console. O header `Authorization` e preflight `OPTIONS` continuarão aceitos.

Swagger, ReDoc e `openapi.json` serão desabilitados fora de `APP_ENV=development`.

## Configuração

```env
# Console
VITE_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
VITE_ALLOWED_EMAIL_DOMAIN=parrottrips.com
VITE_API_URL=https://api.exemplo.com
VITE_ENABLE_CONSOLE_LOCAL=false

# Backend
GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
ALLOWED_EMAIL_DOMAIN=parrottrips.com
CORS_ALLOWED_ORIGINS=https://parrot-trips.netlify.app,https://console.exemplo.com
APP_ENV=production
ENABLE_CONSOLE_LOCAL=false
```

O mesmo OAuth Web Client ID será usado no frontend e backend. O Client ID é público; nenhum client secret será criado.

## Testes

### Backend

- token ausente;
- token expirado;
- audience, issuer ou assinatura incorretos;
- token malformado;
- `email_verified=false`;
- domínio de e-mail incorreto;
- `hd` ausente ou incorreto;
- `sub` ausente;
- configuração ausente;
- bypass local válido e tentativa de ativá-lo em produção;
- token ausente de logs e mensagens de erro;
- router inteiro protegido;
- fase publicada não pode ser excluída;
- validações de campos, datas e URLs;
- rollback integral quando uma parte do salvamento falha.

### Console

- login Google e logout;
- restauração e expiração do `sessionStorage`;
- configuração obrigatória em produção;
- Bearer em todas as chamadas protegidas;
- limpeza da sessão no 401;
- 401 atrasado não apaga credencial nova;
- estados 403 e 503;
- fase publicada somente leitura;
- confirmação de exclusão;
- salvamento por request atômico;
- bloqueio durante operações e feedback ao usuário.

As suítes atuais do console, do CRUD e do JWT interno permanecem como regressão.

## Deploy e rollback

Não haverá migration nem edição de conteúdo em produção durante a implantação.

Ordem de publicação:

1. Criar um OAuth Client do tipo Web application, com audience Internal quando disponível.
2. Cadastrar a origem JavaScript do console; não cadastrar redirect URI nem client secret.
3. Configurar as variáveis do backend e do Netlify.
4. Publicar o backend.
5. Validar `/health`, rejeição sem token e preservação do login do app atual.
6. Publicar o console.
7. Executar smoke test com uma conta `@parrottrips.com`, sem alterar conteúdo real.

Rollback:

- restaurar a revisão anterior do Cloud Run;
- restaurar o deploy anterior do Netlify;
- como não há migration nem transformação de dados, nenhuma reversão de banco é necessária.

## Critérios de aceite

1. Uma conta válida `@parrottrips.com` entra no console com Google e acessa todas as rotas.
2. Contas pessoais ou de outro domínio recebem 403, mesmo que contornem o frontend.
3. Tokens inválidos não alcançam os serviços do console.
4. O app do viajante e o fluxo OTP existente continuam funcionando.
5. Fases publicadas não podem ser editadas ou excluídas.
6. Um salvamento nunca deixa fase, checklist e links em estados parciais.
7. O console é recuperável por rollback de deploy, sem intervenção no banco.

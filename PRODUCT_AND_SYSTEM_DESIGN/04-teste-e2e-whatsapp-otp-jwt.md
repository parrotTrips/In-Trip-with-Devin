# Teste E2E: WhatsApp OTP + JWT

## Resultado

Fluxo completo validado em 2026-05-19. Todos os 6 passos do teste passaram com sucesso usando o backend local conectado ao Supabase e a WhatsApp Cloud API da Meta.

## O que foi testado

```
[1] Backend respondeu em /healthz                          ✅
[2] OTP enviado via WhatsApp (código chegou no celular)    ✅
[3] OTP validado → JWT gerado                              ✅
[4] Rota protegida SEM token → 401                         ✅
[5] Rota protegida COM token válido → passou (404)         ✅
[6] Token inválido → 401                                   ✅
```

O passo 5 retornou 404 porque o `trip_id=test` não existe no banco — o JWT foi aceito pelo middleware, que é o que importa validar.

## Como reproduzir

```bash
cd backend
source env/bin/activate

# Terminal 1 — backend
make dev

# Terminal 2 — teste
make e2e PHONE=+5512991296651
```

## Configuração usada

| Variável | Valor |
|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | `1085386851333264` (conta de teste Meta) |
| `WHATSAPP_TEMPLATE_NAME` | `jaspers_market_order_confirmation_v1` (sandbox temporário) |
| `WHATSAPP_TEMPLATE_LANGUAGE` | `en_US` |
| `JWT_SECRET` | placeholder (trocar em produção) |

## Fluxo técnico completo

```
Usuário digita telefone no app
        ↓
POST /auth/request-otp
        ↓
Backend gera código de 6 dígitos, salva em otp_codes (Supabase)
        ↓
Backend chama WhatsApp Cloud API com o template configurado
        ↓
Código chega no WhatsApp do usuário
        ↓
Usuário digita o código no app
        ↓
POST /auth/verify-otp
        ↓
Backend valida código → cria usuário na tabela users (se primeiro acesso)
        ↓
Backend assina JWT com { sub: user_id, phone, exp: +14 dias }
        ↓
Frontend armazena { userId, phone, name, token } no localStorage
        ↓
Todas as chamadas seguintes incluem Authorization: Bearer <token>
        ↓
JWTAuthMiddleware valida o token em cada request não-pública
        ↓
401 se ausente, expirado ou inválido
```

## Limitações do ambiente de teste

- A conta Meta usada é o **sandbox de teste** (Test WhatsApp Business Account).
- Só envia mensagens para números adicionados manualmente na lista de destinatários de teste no painel Meta.
- Não tem permissão para criar templates próprios — por isso o template temporário `jaspers_market_order_confirmation_v1` foi usado no lugar do `intripauth`.
- O código OTP aparece no campo "número do pedido" da mensagem de confirmação de pedido (template de mercado da Meta) — funcional para testes, não para produção.

## O que muda em produção

Quando a conta WhatsApp Business real estiver configurada, basta atualizar o `backend/.env`:

```env
WHATSAPP_PHONE_NUMBER_ID=<id_do_numero_real>
WHATSAPP_ACCESS_TOKEN=<token_permanente>
WHATSAPP_TEMPLATE_NAME=intripauth
WHATSAPP_TEMPLATE_LANGUAGE=pt_BR
JWT_SECRET=<string_aleatoria_forte_minimo_32_chars>
```

O código do backend já está preparado para o template `intripauth` — a função `_build_template_components()` em `backend/app/services/auth_service.py` usa o branch correto automaticamente quando `WHATSAPP_TEMPLATE_NAME=intripauth`.

# Conexão com o Supabase — Diagnóstico e Correção

> Registrado em maio 2026 após falha de conexão ao banco.

---

## Sintoma

Qualquer tentativa de conectar ao banco retornava:

```
socket.gaierror: [Errno 8] nodename nor servname provided, or not known
```

O host `db.zotyldoqjjqjrdnhdisw.supabase.co` não resolvia via DNS, mesmo com o projeto aparecendo como **Healthy** e **PRO** no dashboard do Supabase.

---

## Causa raiz

O host `db.<ref>.supabase.co` é a **conexão direta ao Postgres**. Em projetos PRO na região São Paulo, essa conexão exige **IPv6**. A rede local não suporta IPv6, então o DNS não retorna nenhum endereço IPv4 para esse host — daí o erro "no answer".

O próprio Supabase documenta isso:

> *"For paid projects, if your network supports IPv6, or you purchased the IPv4 add-on, use the dedicated direct connection. Otherwise, use the shared pooler."*

O projeto não tem o add-on IPv4 contratado e a rede não suporta IPv6 → conexão direta não funciona.

---

## Solução: usar o connection pooler (Supavisor)

O Supabase oferece um **pooler** próprio (Supavisor) em IPv4 que serve como proxy para o Postgres. Ele tem dois modos:

| modo | porta | parâmetro extra | quando usar |
|---|---|---|---|
| Transaction (pgbouncer) | 6543 | `?pgbouncer=true` | APIs stateless, alta concorrência |
| **Session** | **5432** | nenhum | **SQLAlchemy, Alembic, prepared statements** |

O projeto usa SQLAlchemy + asyncpg, que depende de prepared statements e sessões persistentes. O modo correto é o **session mode (porta 5432)**, sem `?pgbouncer=true`.

---

## Diferença entre os três tipos de URL do Supabase

| tipo | URL | usa para |
|---|---|---|
| API REST | `https://zotyldoqjjqjrdnhdisw.supabase.co` | chamadas HTTP ao PostgREST (SDK JS/Python) |
| Conexão direta | `db.zotyldoqjjqjrdnhdisw.supabase.co:5432` | Postgres direto via IPv6 (ou IPv4 add-on) |
| **Pooler (session)** | `aws-1-sa-east-1.pooler.supabase.com:5432` | **Postgres via pooler IPv4 — usado neste projeto** |

O SDK Flask/Supabase que aparece na documentação usa a **API REST**, não o Postgres direto. Não é compatível com a arquitetura deste projeto (FastAPI + SQLAlchemy + asyncpg).

---

## O que muda na configuração

**Arquivo:** `backend/.env`  
**Chave:** `DATABASE_URL`

| campo | antes (quebrado) | depois (correto) |
|---|---|---|
| driver | `postgresql+asyncpg` | `postgresql+asyncpg` (mesmo) |
| usuário | `postgres` | `postgres.zotyldoqjjqjrdnhdisw` |
| senha | (mesma) | (mesma) |
| host | `db.zotyldoqjjqjrdnhdisw.supabase.co` | `aws-1-sa-east-1.pooler.supabase.com` |
| porta | `5432` | `5432` (mesmo) |
| banco | `postgres` | `postgres` (mesmo) |
| parâmetros extras | nenhum | nenhum |

Formato final:
```
DATABASE_URL=postgresql+asyncpg://postgres.zotyldoqjjqjrdnhdisw:[SENHA]@aws-1-sa-east-1.pooler.supabase.com:5432/postgres
```

**Apenas `backend/.env` precisa ser alterado.** Nenhum arquivo `.py` tem o host hardcoded — todos leem via `os.environ.get("DATABASE_URL")` em `backend/app/core/config.py`.

---

## Como obter a URL correta no Supabase

1. Dashboard do projeto → botão **Connect** (canto superior direito)
2. Aba **Connection string**
3. Modo: **Session**
4. Copiar a string — ela já vem com o host e usuário corretos, só substituir `[YOUR-PASSWORD]`

---

## Alteração aplicada

**Data:** maio 2026  
**Arquivo alterado:** `backend/.env`

```
# antes
DATABASE_URL=postgresql+asyncpg://postgres:...@db.zotyldoqjjqjrdnhdisw.supabase.co:5432/postgres

# depois
DATABASE_URL=postgresql+asyncpg://postgres.zotyldoqjjqjrdnhdisw:...@aws-1-sa-east-1.pooler.supabase.com:5432/postgres
```

Conexão confirmada funcionando via `gen_dev_users.py` após a troca.

---

## Como confirmar que a conexão voltou a funcionar

```bash
cd backend
env/bin/python3 scripts/gen_dev_users.py
```

Se listar as viagens sem erro, a conexão está funcionando.

---

## Outros arquivos que usam DATABASE_URL

Todos leem do `.env` via `dotenv` — nenhum tem o host hardcoded:

| arquivo | como usa |
|---|---|
| `backend/app/core/config.py` | `os.environ.get("DATABASE_URL")` — fonte central |
| `backend/scripts/seed_placeholder_trip.py` | `os.environ.get("DATABASE_URL")` |
| `backend/scripts/gen_dev_users.py` | `os.environ.get("DATABASE_URL")` |
| `backend/tests/conftest.py` | `os.environ.get("DATABASE_URL")` |

Alterar o `.env` corrige todos de uma vez.

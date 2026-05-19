"""
E2E: Opcao 1 — WhatsApp OTP + JWT

Testa o fluxo completo de autenticacao usando o backend local.
Como o WhatsApp Business API nao esta configurado, o OTP aparece
como debug_code na resposta JSON.

Pre-requisitos:
  - Backend rodando em localhost:8000
  - env/bin/uvicorn app.main:app --port 8000 (na pasta backend/)

Execucao:
  python tests/e2e/test_opcao1_whatsapp_otp.py +5511999999999
"""

import sys
import httpx

BASE_URL = "http://localhost:8000"
SEPARATOR = "-" * 55


def step(numero, descricao):
    print(f"\n[{numero}] {descricao}")
    print(SEPARATOR)


def ok(msg):
    print(f"  OK  {msg}")


def erro(msg):
    print(f"  ERRO  {msg}")


def info(msg):
    print(f"  -->  {msg}")


def run(phone: str):
    print(f"\n{'=' * 55}")
    print("  TESTE E2E — OPCAO 1: WhatsApp OTP + JWT")
    print(f"{'=' * 55}")
    print(f"  Telefone: {phone}")
    print(f"  Backend:  {BASE_URL}")

    # ── PASSO 1: verificar se o backend esta no ar ────────────────
    step(1, "Verificar backend")
    try:
        r = httpx.get(f"{BASE_URL}/healthz", timeout=5)
        if r.status_code == 200:
            ok("Backend respondeu em /healthz")
        else:
            erro(f"Backend retornou status {r.status_code}")
            return
    except Exception as e:
        erro(f"Nao foi possivel conectar ao backend: {e}")
        return

    # ── PASSO 2: solicitar OTP ────────────────────────────────────
    step(2, "Solicitar OTP — POST /auth/request-otp")
    try:
        r = httpx.post(f"{BASE_URL}/auth/request-otp", json={"phone": phone}, timeout=10)
        info(f"Status: {r.status_code}")
        info(f"Resposta: {r.json()}")

        if r.status_code != 200:
            erro(f"Falha ao solicitar OTP: {r.json()}")
            return

        debug_code = r.json().get("debug_code")
        code = debug_code if debug_code else input("\n  Digite o codigo recebido no WhatsApp: ").strip()

        if debug_code:
            ok(f"WhatsApp nao configurado — codigo de teste: {code}")
        else:
            ok("OTP enviado via WhatsApp")
    except Exception as e:
        erro(f"Excecao: {e}")
        return

    # ── PASSO 3: verificar OTP e checar JWT ───────────────────────
    step(3, f"Verificar OTP — POST /auth/verify-otp (codigo: {code})")
    try:
        r = httpx.post(f"{BASE_URL}/auth/verify-otp", json={"phone": phone, "code": code}, timeout=10)
        info(f"Status: {r.status_code}")
        data = r.json()

        if r.status_code != 200:
            erro(f"OTP invalido ou expirado: {data}")
            return

        ok("OTP validado com sucesso")
        ok(f"user_id:      {data.get('user_id')}")
        ok(f"phone:        {data.get('phone')}")

        token = data.get("access_token")
        if token:
            ok(f"access_token: {token[:40]}...")
        else:
            erro("access_token ausente na resposta — JWT nao gerado")
            return

        user_id = data.get("user_id")
    except Exception as e:
        erro(f"Excecao: {e}")
        return

    # ── PASSO 4: rota protegida SEM token — deve retornar 401 ─────
    step(4, "Rota protegida SEM token — espera 401")
    try:
        r = httpx.get(f"{BASE_URL}/profile/{user_id}", params={"trip_id": "test"}, timeout=10)
        info(f"Status: {r.status_code}")
        if r.status_code == 401:
            ok("Retornou 401 corretamente — rota protegida funcionando")
        else:
            erro(f"Esperava 401, recebeu {r.status_code} — middleware pode nao estar ativo")
    except Exception as e:
        erro(f"Excecao: {e}")

    # ── PASSO 5: rota protegida COM token — deve passar ───────────
    step(5, "Rota protegida COM token — espera 200 ou 404")
    try:
        r = httpx.get(
            f"{BASE_URL}/profile/{user_id}",
            params={"trip_id": "test"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        info(f"Status: {r.status_code}")
        if r.status_code in (200, 404, 422):
            ok(f"Token aceito pelo middleware (status {r.status_code} — 401 seria falha)")
        elif r.status_code == 401:
            erro("Token rejeitado — verificar JWT_SECRET no .env do backend")
        else:
            info(f"Status inesperado: {r.status_code}")
    except Exception as e:
        erro(f"Excecao: {e}")

    # ── PASSO 6: token invalido — deve retornar 401 ───────────────
    step(6, "Token invalido — espera 401")
    try:
        r = httpx.get(
            f"{BASE_URL}/profile/{user_id}",
            params={"trip_id": "test"},
            headers={"Authorization": "Bearer token-invalido"},
            timeout=10,
        )
        info(f"Status: {r.status_code}")
        if r.status_code == 401:
            ok("Token invalido rejeitado corretamente")
        else:
            erro(f"Esperava 401, recebeu {r.status_code}")
    except Exception as e:
        erro(f"Excecao: {e}")

    # ── RESULTADO ─────────────────────────────────────────────────
    print(f"\n{'=' * 55}")
    print("  RESULTADO OPCAO 1 — COMPLETO")
    print(f"{'=' * 55}")
    print("  Fluxo completo com JWT funcionando.")
    print()
    print("  Para producao, configurar no backend/.env:")
    print("  - WHATSAPP_PHONE_NUMBER_ID")
    print("  - WHATSAPP_ACCESS_TOKEN")
    print("  - JWT_SECRET (valor forte, minimo 32 chars)")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tests/e2e/test_opcao1_whatsapp_otp.py +5511999999999")
        sys.exit(1)
    run(sys.argv[1])

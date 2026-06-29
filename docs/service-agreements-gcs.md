# Service Agreements no Google Cloud Storage

Este documento explica como armazenar PDFs de Service Agreement em um bucket privado da GCP e entregar o arquivo ao app por URL assinada temporária.

## Decisão

Service Agreements devem ficar em bucket privado, não em URL pública fixa.

Motivo: contratos podem conter dados pessoais. Em produção, o ideal é que o PDF não fique acessível para qualquer pessoa que descubra o link.

## Bucket

Projeto GCP:

```text
jogo-da-vida-497700
```

Bucket:

```text
gs://parrot-trips-service-agreements-prod
```

Região:

```text
southamerica-east1
```

## Organização por Viagem

Use sempre este padrão:

```text
gs://parrot-trips-service-agreements-prod/trips/<trip_uuid>/service-agreement.pdf
```

Exemplo da viagem de teste:

```text
gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf
```

## Como Subir um PDF

No root do repositório:

```bash
gcloud config set project jogo-da-vida-497700

gcloud storage cp \
  service_agreements/parrot_test_service_agreement.pdf \
  gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf
```

## Como Criar o Bucket

Rodar uma vez:

```bash
gcloud storage buckets create gs://parrot-trips-service-agreements-prod \
  --project=jogo-da-vida-497700 \
  --location=southamerica-east1 \
  --uniform-bucket-level-access
```

O bucket deve continuar privado. Não rode comandos como `allUsers` ou `public-read` para esse bucket.

## Como Ligar o PDF a uma Viagem

Na aba `Viagens` da planilha de viajantes, coluna `service_agreement_url`, coloque o caminho GCS:

```text
gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf
```

Depois rode o import da viagem:

```bash
cd backend
poetry run python scripts/import_trip_content.py --trip-uuid TEST-2026-FULL
```

Também é possível atualizar direto no Supabase em `wetravel_trips.service_agreement_url`, mas a planilha é a fonte operacional preferida.

## Como o App Recebe o PDF

O app não recebe o caminho `gs://...` diretamente.

Fluxo:

1. Supabase guarda `gs://...` em `wetravel_trips.service_agreement_url`.
2. O app chama `GET /me/trip`.
3. O backend identifica que o valor começa com `gs://`.
4. O backend gera uma signed URL temporária da GCP.
5. O app recebe uma URL HTTPS temporária em `service_agreement_url`.
6. O botão `View Service Agreement` abre essa URL.

Por padrão, a URL assinada dura 30 minutos.

## Permissões Necessárias

O serviço que roda o backend precisa conseguir assinar/ler objetos do bucket.

Em Cloud Run, isso normalmente significa garantir que a service account do backend tenha acesso ao bucket, por exemplo:

```bash
gcloud storage buckets add-iam-policy-binding gs://parrot-trips-service-agreements-prod \
  --member="serviceAccount:<SERVICE_ACCOUNT_DO_CLOUD_RUN>" \
  --role="roles/storage.objectViewer"
```

Além de ler o objeto, o backend precisa assinar a URL temporária usando IAM Credentials. Para isso, a service account do Cloud Run precisa poder assinar blobs. No caso do backend atual:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  428743191336-compute@developer.gserviceaccount.com \
  --project=jogo-da-vida-497700 \
  --member="serviceAccount:428743191336-compute@developer.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

O backend também deve receber a variável:

```text
SERVICE_ACCOUNT_EMAIL=428743191336-compute@developer.gserviceaccount.com
```

Se a geração de signed URL falhar em produção, verificar:

- se o backend está usando a service account correta;
- se `SERVICE_ACCOUNT_EMAIL` está configurado;
- se a service account tem permissão no bucket;
- se a service account tem `roles/iam.serviceAccountTokenCreator`;
- se o objeto existe no caminho esperado;
- se o valor salvo no Supabase começa com `gs://` e tem bucket + caminho.

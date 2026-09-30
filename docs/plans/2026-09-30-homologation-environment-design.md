# Ambiente de homologacao

## Objetivo

Criar um ambiente permanente de homologacao isolado de producao, promovendo para producao somente o mesmo codigo que ja foi validado.

## Fluxo de branches

- `main` representa producao.
- `homologacao` representa o ambiente de homologacao.
- Mudancas entram primeiro em `homologacao` e chegam a `main` por pull request.
- Correcoes urgentes feitas em `main` devem voltar para `homologacao` logo depois.

## Recursos por ambiente

Homologacao tera recursos independentes:

- um projeto Supabase Free em uma organizacao Free separada;
- um servico Cloud Run `parrot-trips-backend-homolog`;
- um site Netlify separado para o frontend;
- variaveis, segredos e JWT exclusivos;
- somente dados ficticios ou anonimizados.

Producao continuara usando os recursos atuais. Nenhum backend ou frontend de homologacao apontara para o banco de producao.

## Deploy e promocao

O deploy sera automatizado por branch quando as credenciais necessarias estiverem disponiveis no GitHub. Um push em `homologacao` atualiza homologacao; um merge em `main` atualiza producao. A imagem do backend sera identificada pelo SHA do commit, permitindo saber exatamente qual versao esta em cada ambiente.

Enquanto a automacao nao estiver configurada, comandos explicitos no `Makefile` permitirao deploy manual sem ambiguidade entre ambientes.

## Banco e migrations

As mesmas migrations Alembic serao executadas primeiro em homologacao e depois em producao. Migrations destrutivas exigem backup e devem ser divididas em etapas retrocompativeis quando possivel. O banco gratuito de homologacao pode pausar por inatividade e ser retomado antes dos testes.

## Seguranca e custos

Segredos nao serao commitados. A criacao do Supabase deve mostrar plano Free e custo zero; qualquer opcao paga interrompe o processo para confirmacao. Integracoes externas de homologacao devem usar credenciais de teste ou permanecer desativadas quando houver risco de enviar mensagens a clientes reais.

## Validacao

Antes de considerar o ambiente pronto, serao validados: migrations, endpoint de saude do backend, CORS, build e acesso do frontend, conexao exclusiva ao banco de homologacao e ausencia de segredos no Git.

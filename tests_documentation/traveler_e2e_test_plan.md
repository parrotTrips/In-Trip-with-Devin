# Teste E2E do Viajante

Este documento é um passo a passo para testar a jornada completa de um viajante, começando na WeTravel e terminando no aplicativo publicado.

O objetivo é responder uma pergunta simples:

> Uma pessoa comprou a viagem, entrou no app e conseguiu usar tudo que precisa como viajante?

Neste primeiro teste, vamos olhar somente o lado do viajante. O fluxo de staff fica para outro documento.

## Informações do Teste

Preencha antes de começar:

| Campo | Valor |
| --- | --- |
| Nome da viagem |  |
| `trip_uuid` da viagem |  |
| Nome do viajante de teste | Marcelo Angelo |
| Telefone do viajante |  |
| Email usado na compra |  |
| Data em que o teste foi feito |  |
| Pessoa que testou |  |
| Link do app | https://parrot-trips-app-286.netlify.app |
| Link do backend | https://parrot-trips-backend-428743191336.southamerica-east1.run.app |

## Antes de Começar

Confirme estes pontos:

- Você consegue acessar a WeTravel.
- Você consegue acessar a planilha de conteúdo dos viajantes.
- Você consegue acessar o Supabase, ou tem alguém técnico disponível para conferir o Supabase.
- O WhatsApp OTP está funcionando para o telefone de teste.
- Você sabe qual telefone será usado pelo Marcelo Angelo.
- Você tem o `trip_uuid` da viagem.

Ponto de atenção importante:

O import de conteúdo da viagem apaga e recria fases, checklist, links, roteiro e atividades daquela viagem. Então, para teste, tudo bem rodar várias vezes. Para uma viagem real com viajantes usando o app, isso precisa ser feito com cuidado.

---

# Parte 1: Criar a Viagem na WeTravel

## Passo 1: Criar ou escolher a viagem

1. Entre na WeTravel.
2. Crie uma viagem de teste ou escolha uma viagem que ainda não esteja sendo usada por viajantes reais.
3. Preencha pelo menos:
   - nome da viagem;
   - data de início;
   - data de fim;
   - preço ou pacote de teste;
   - produto que o viajante poderá comprar.
4. Salve a viagem.

## O que conferir

- A viagem aparece na WeTravel.
- A viagem tem nome claro.
- A viagem tem data de início e fim.
- A viagem tem um pacote/produto comprável.

## Se der errado, anotar

- O que você tentou fazer.
- Qual campo não conseguiu preencher.
- Print da tela de erro, se existir.

---

# Parte 2: Simular a Compra do Viajante

## Passo 2: Fazer uma compra de teste

1. Abra a página pública da viagem na WeTravel.
2. Faça uma compra como se fosse o Marcelo Angelo.
3. Use o email de teste escolhido.
4. Use o nome `Marcelo Angelo`.
5. Finalize a compra usando o método de teste disponível na WeTravel.

## O que conferir

- A compra aparece como criada/confirmada na WeTravel.
- O nome do comprador ou participante está como Marcelo Angelo.
- O email usado na compra está correto.
- A compra está ligada à viagem certa.

## Se der errado, anotar

- Se a compra não finalizou.
- Se a compra ficou com status errado.
- Se o email ou nome ficou diferente do esperado.

---

# Parte 3: Conferir se a Compra Chegou na Base

## Passo 3: Confirmar dados no sistema

Depois da compra, precisamos confirmar se a informação saiu da WeTravel e chegou na base usada pelo app.

Peça para alguém técnico conferir no Supabase se existem dados novos para:

- a viagem criada;
- o email do Marcelo Angelo;
- a compra feita na WeTravel.

Tabelas/pontos que podem ser conferidos:

- `wetravel_trips`;
- `wetravel_bookings`;
- `wetravel_payments`;
- `wetravel_order_options`;
- `trip_travelers`;
- `wetravel_participant_phones`.

## O que conferir

- A viagem existe em `wetravel_trips`.
- A compra existe nas tabelas da WeTravel.
- O Marcelo Angelo está vinculado à viagem.
- O telefone do Marcelo Angelo está vinculado ao email usado na compra.

## Se der errado, anotar

- A viagem apareceu no Supabase?
- A compra apareceu no Supabase?
- O email apareceu?
- O telefone apareceu?
- O viajante apareceu em `trip_travelers`?

---

# Parte 4: Preencher a Planilha dos Viajantes

## Passo 4: Preencher a aba `Viagens`

Na planilha de conteúdo dos viajantes, encontre a aba `Viagens`.

Preencha uma linha para a viagem de teste.

Campos importantes:

- `trip_uuid`;
- nome da viagem;
- data de início;
- data de fim;
- link do Service Agreement, se existir.

## O que conferir

- O `trip_uuid` está exatamente igual ao da WeTravel/Supabase.
- Não tem espaço antes ou depois do `trip_uuid`.
- As datas estão no formato esperado pela planilha.

## Passo 5: Preencher as fases pré-viagem

Na aba `Fases`, preencha as etapas que aparecem antes da viagem começar.

Exemplos:

- documentos;
- visto;
- vacinas;
- seguro viagem;
- mala;
- chegada.

Cada linha deve representar uma fase do app.

## O que conferir

- Toda linha tem o `trip_uuid`.
- A ordem das fases faz sentido.
- Os títulos estão escritos de forma clara para o viajante.
- Existe pelo menos uma fase marcada como ritmo ideal, se a planilha tiver esse campo.

## Passo 6: Preencher checklist

Na aba `Checklist`, coloque tarefas que o viajante pode marcar como feitas.

Exemplos:

- enviar passaporte;
- contratar seguro viagem;
- preencher dados do voo;
- conferir documentos.

## O que conferir

- O nome da fase no checklist bate com o nome da fase na aba `Fases`.
- O checklist não tem tarefas duplicadas sem querer.
- O texto está simples e direto.

## Passo 7: Preencher links úteis

Na aba `Links`, coloque links que aparecem dentro de cada fase.

Exemplos:

- link do formulário;
- link do seguro;
- link do consulado;
- link do documento.

## O que conferir

- O link abre no navegador.
- O link está na fase correta.
- O texto do botão explica para onde o viajante vai.

## Passo 8: Preencher roteiro da viagem

Na aba `Roteiro`, preencha os dias da viagem e as atividades.

Campos importantes:

- `trip_uuid`;
- dia;
- data;
- título do dia;
- subtítulo do dia;
- nome da atividade;
- tipo da atividade;
- duração;
- descrição curta;
- informação prática;
- preço, se tiver.

## O que conferir

- Cada dia da viagem tem pelo menos uma linha.
- As datas do roteiro batem com as datas da viagem.
- As atividades estão na ordem correta.
- O texto foi escrito para o viajante, não para a operação interna.

---

# Parte 5: Importar a Planilha para o Supabase

## Passo 9: Importar conteúdo da viagem

Depois que a planilha estiver preenchida, rode o import da viagem.

Se houver botão na planilha:

1. Clique no botão de importação.
2. Informe o `trip_uuid`, se o botão pedir.
3. Aguarde a mensagem de sucesso.

Se for via terminal, peça para alguém técnico rodar:

```bash
cd backend
poetry run python scripts/import_trip_content.py --trip-uuid SEU_TRIP_UUID
```

Se for via backend publicado:

```bash
curl -sS -X POST "https://parrot-trips-backend-428743191336.southamerica-east1.run.app/admin/trips/import" \
  -H "Content-Type: application/json" \
  -d '{"trip_uuid":"SEU_TRIP_UUID"}'
```

Troque `SEU_TRIP_UUID` pelo código real da viagem.

## O que conferir

- O import terminou com sucesso.
- A resposta mostra quantidade de fases.
- A resposta mostra quantidade de dias.
- A resposta mostra quantidade de atividades.
- Não apareceu erro de permissão da planilha.

## Se der errado, anotar

- Mensagem de erro completa.
- Qual botão ou comando foi usado.
- Qual `trip_uuid` foi importado.

---

# Parte 6: Entrar no Aplicativo como Viajante

## Passo 10: Abrir o app

1. Abra: https://parrot-trips-app-286.netlify.app
2. Digite o telefone do Marcelo Angelo.
3. Clique para receber o código por WhatsApp.
4. Espere o código chegar.
5. Digite o código no app.
6. Entre no aplicativo.

## O que conferir

- O código chegou por WhatsApp.
- O login funcionou.
- O app abriu na visão de viajante.
- O nome ou telefone do Marcelo aparece corretamente.
- A viagem correta aparece no app.

## Se der errado, anotar

- O código chegou?
- Apareceu `Load failed`?
- Apareceu erro de login?
- O telefone foi digitado com DDD correto?

---

# Parte 7: Testar o App Antes da Viagem

## Passo 11: Conferir tela inicial

Na tela inicial, confira se a viagem parece correta.

## O que conferir

- Nome da viagem correto.
- Status de pré-viagem.
- Fases pré-viagem aparecem.
- Ordem das fases está correta.
- Progresso/checklist aparece de forma compreensível.

## Passo 12: Abrir cada fase pré-viagem

Entre em cada fase e confira:

- título;
- descrição;
- checklist;
- links;
- botão de marcar como completo, se existir.

## O que conferir

- O texto é o mesmo que foi preenchido na planilha.
- Os checklists podem ser marcados.
- Os links abrem.
- Ao voltar para a tela inicial, o progresso atualiza.

## Passo 13: Testar Perfil

Abra a área de perfil do viajante.

## O que conferir

- Nome do viajante.
- Telefone.
- Dados de pacote/compra, se aparecerem.
- Campos editáveis, se houver.
- Botão de salvar.

## Passo 14: Testar QRCode

Abra a aba `QRCode` ou `My QRCode`.

## O que conferir

- O QRCode aparece.
- O QRCode não aparece quebrado.
- O QRCode pertence ao viajante logado.
- Ao sair e entrar de novo, o QRCode continua aparecendo.

Ponto importante:

O QRCode do viajante deve ser estável. Ele não deve sumir nem mudar sem motivo.

---

# Parte 8: Virar a Viagem para In-Trip

## Passo 15: Colocar a viagem em modo in-trip

Quando quiser testar a experiência durante a viagem, precisamos mudar a viagem para modo `in-trip`.

Se houver botão na planilha/admin:

1. Clique no botão de iniciar viagem.
2. Informe o `trip_uuid`, se pedir.
3. Aguarde a mensagem de sucesso.

Se for via backend publicado:

```bash
curl -sS -X POST "https://parrot-trips-backend-428743191336.southamerica-east1.run.app/admin/trips/start-trip" \
  -H "Content-Type: application/json" \
  -d '{"trip_uuid":"SEU_TRIP_UUID"}'
```

## O que conferir

- A resposta mostra `mode: in-trip`.
- Ao atualizar o app, a experiência muda para durante a viagem.
- O roteiro da viagem aparece.

## Se der errado, anotar

- A resposta do botão/comando.
- Se o app continuou em pré-viagem.
- Se a viagem correta foi usada.

---

# Parte 9: Simular a Passagem dos Dias

## Passo 16: Simular o dia atual da viagem

Para não precisar esperar dias reais passarem, existe um script interno que muda as datas das fases da viagem no Supabase.

Peça para alguém técnico rodar:

```bash
cd backend
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --day 1
```

Exemplos:

```bash
# Simular que nenhum dia começou ainda
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --day 0

# Simular Dia 1
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --day 1

# Simular Dia 3
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --day 3

# Resetar datas para a data original da viagem
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --reset
```

Importante:

- `--day 0` significa que nenhum dia começou.
- `--day 1` significa que o Dia 1 já começou.
- `--day 3` significa que os Dias 1, 2 e 3 já começaram.
- `--reset` volta as datas usando a data de início da viagem cadastrada.

## O que conferir

- O comando mostra quantos dias existem na viagem.
- O comando mostra qual dia foi simulado.
- Ao atualizar o app, a barra/progresso muda.
- O roteiro do dia correto aparece como esperado.

## Se der errado, anotar

- Qual `--day` foi usado.
- Quantos dias a viagem tem.
- O que apareceu no app depois de atualizar.

---

# Parte 10: Testar o App Durante a Viagem

## Passo 17: Conferir roteiro

No app, confira o roteiro depois que a viagem estiver em modo `in-trip`.

## O que conferir

- Os dias aparecem na ordem correta.
- As atividades aparecem dentro do dia certo.
- O texto das atividades bate com a planilha.
- Duração e preço aparecem quando foram preenchidos.
- Informações desnecessárias não aparecem em lugar errado.

## Passo 18: Abrir atividades

Abra algumas atividades do roteiro.

## O que conferir

- Nome da atividade correto.
- Descrição correta.
- Informações práticas corretas.
- Preço correto, se houver.
- Atividade opcional aparece como opcional, se esse campo estiver sendo usado.

## Passo 19: Testar avanço de dias

Rode a simulação para mais de um dia.

Exemplo:

```bash
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --day 2
```

Atualize o app.

Depois rode:

```bash
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --day 4
```

Atualize o app de novo.

## O que conferir

- O app muda conforme o dia simulado.
- O progresso não fica acima de 100%.
- O roteiro continua abrindo corretamente.
- O QRCode do viajante continua disponível.

---

# Parte 11: Encerrar o Teste

## Passo 20: Resetar a viagem, se necessário

Se quiser deixar a viagem pronta para outro teste, peça para alguém técnico rodar:

```bash
cd backend
poetry run python scripts/simulate_trip_day.py --trip-uuid SEU_TRIP_UUID --reset
```

Se quiser voltar a viagem para pré-viagem e limpar progresso de teste:

```bash
curl -sS -X POST "https://parrot-trips-backend-428743191336.southamerica-east1.run.app/admin/trips/reset-trip" \
  -H "Content-Type: application/json" \
  -d '{"trip_uuid":"SEU_TRIP_UUID"}'
```

## O que conferir

- A viagem voltou para um estado previsível.
- O app não ficou preso em um dia simulado errado.
- O progresso de teste foi limpo, se esse era o objetivo.

---

# Checklist Final do Teste

Marque ao final:

- [ ] Viagem criada ou escolhida na WeTravel.
- [ ] Compra de teste feita.
- [ ] Compra apareceu na base.
- [ ] Telefone do viajante foi vinculado ao email da compra.
- [ ] Conteúdo da viagem foi preenchido na planilha.
- [ ] Conteúdo foi importado para o Supabase.
- [ ] Login por WhatsApp funcionou.
- [ ] Tela inicial do viajante abriu.
- [ ] Fases pré-viagem apareceram.
- [ ] Checklist funcionou.
- [ ] Links abriram.
- [ ] Perfil abriu.
- [ ] QRCode apareceu.
- [ ] Viagem foi colocada em modo `in-trip`.
- [ ] Roteiro apareceu.
- [ ] Simulação de dias funcionou.
- [ ] QRCode continuou aparecendo durante a viagem.

## Modelo para Registrar Problemas

Use este formato para cada problema:

```text
Problema:

Onde aconteceu:

Passo do documento:

O que eu esperava:

O que aconteceu:

Telefone usado:

Trip UUID:

Print ou vídeo:

Prioridade:
```

## Como decidir prioridade

Alta:

- impede login;
- impede o viajante de ver a viagem;
- QRCode não aparece;
- dados da viagem aparecem errados;
- compra não conecta com o viajante.

Média:

- texto aparece em lugar errado;
- checklist não atualiza;
- link abre errado;
- roteiro aparece, mas com alguma informação faltando.

Baixa:

- ajuste visual;
- texto pode ficar mais claro;
- ordem de informação poderia melhorar.


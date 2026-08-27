# Guia de Validacao - Viagem Interna Parrot

Este guia serve para orientar o teste completo da viagem interna da Parrot no aplicativo, cobrindo a experiencia de viajante e de staff.

## Informacoes gerais

| Campo | Valor |
| --- | --- |
| Nome da viagem | Viagem Interna Parrot |
| Periodo de pre-trip | 18/08/2026 a 23/08/2026 |
| Periodo in-trip | 24/08/2026 a 01/09/2026 |
| App | https://parrot-trips.netlify.app |
| Objetivo principal | Validar login, perfil, pacotes, roteiro, mensagens, QR check-in, atividades restritas, feedback e visao de staff |

## Objetivo do teste

Validar se o app esta pronto para operar uma viagem real, olhando os dois lados da experiencia:

- **Traveler:** o viajante consegue entrar, ver seus dados, acompanhar o pre-trip, acessar QR Code, ver roteiro, receber mensagens, consultar informacoes e enviar feedback.
- **Staff:** a equipe consegue operar a viagem, visualizar contatos, mandar mensagens, alternar para visao de viajante, escanear QR Codes e controlar atividades inclusas, opcionais e restritas.

## Papeis no teste

| Papel | O que deve testar |
| --- | --- |
| Traveler | Login, perfil, pacote, QR Code, checklist, progresso, roteiro, informacoes, FAQ, recomendacoes, mensagens e feedback |
| Staff | Tela operacional, contatos, mensagens, traveler view, QR scanner, check-ins, atividades restritas e contadores |

## Antes de comecar

Confirme estes pontos antes de pedir para as pessoas testarem:

- A viagem aparece no app como **Viagem Interna Parrot**.
- As datas estao configuradas para pre-trip de **18/08/2026 a 23/08/2026**.
- O periodo in-trip esta configurado de **24/08/2026** a **01/09/2026**.
- Os viajantes de teste conseguem fazer login com seus telefones.
- Os staffs conseguem fazer login e cair na visao de staff.
- Os QR Codes dos viajantes estao disponiveis.
- As atividades restritas possuem uma lista menor de viajantes permitidos.
- Os links de package, service agreement, cancelamento e recomendacoes estao funcionando.

## Cronograma de validacao

| Data | Fase | Foco do teste |
| --- | --- | --- |
| 18/08/2026 | Pre-trip | Login, acesso inicial, perfil e pacote |
| 19/08/2026 | Pre-trip | Checklist, fases, progresso e QR Code |
| 20/08/2026 | Pre-trip | Informacoes, FAQ, recomendacoes e links |
| 21/08/2026 | Pre-trip | Mensagens de staff e visualizacao pelo traveler |
| 22/08/2026 | Pre-trip | Feedback do app e revisao de dados pessoais |
| 23/08/2026 | Pre-trip | Reteste geral antes de iniciar viagem |
| 24/08/2026 | In-trip Dia 1 | Roteiro, progresso, check-ins e atividades restritas |
| 25/08/2026 | In-trip Dia 2 | Atividades opcionais, feedback final e validacao operacional |
| 26/08/2026 a 01/09/2026 | In-trip estendido | Retestes internos da Parrot no aplicativo |

## Validacao como traveler

Cada pessoa testando como traveler deve usar o proprio telefone de teste e registrar o que aconteceu.

### 1. Login e acesso

Checklist:

- Entrar no app pelo link oficial.
- Fazer login com o telefone correto.
- Confirmar que entrou na viagem **Viagem Interna Parrot**.
- Confirmar que nao apareceu tela de staff por engano.
- Fechar e abrir o app novamente para confirmar que a sessao continua funcionando.

Resultado esperado:

- O traveler entra diretamente na experiencia de viajante.
- A viagem exibida e a viagem correta.
- O app nao mostra funcoes operacionais de staff.

### 2. My Profile

Checklist:

- Abrir **My Profile**.
- Conferir nome, telefone e email, quando disponivel.
- Conferir **Products & Payment**.
- Validar package comprado.
- Validar add-ons, se existirem para aquele traveler.
- Validar valor pago, quando exibido.
- Abrir links relacionados a package e service agreement.
- Conferir o link de **Transfer or Cancel your Package**.

Resultado esperado:

- Os dados do traveler aparecem corretamente.
- Package e add-ons batem com a base da viagem.
- Links abrem no navegador sem erro.
- O link de cancelamento/transferencia aponta para a pagina correta.

### 3. Registration Details

Checklist:

- Abrir os campos de perfil.
- Preencher ou revisar nome preferido.
- Preencher ou revisar restricoes alimentares.
- Preencher ou revisar enjoo.
- Preencher ou revisar dados de passaporte, se o campo estiver disponivel.
- Salvar as informacoes.
- Sair e voltar para confirmar que os dados persistiram.

Resultado esperado:

- O traveler consegue preencher dados pessoais.
- Os dados continuam salvos depois de recarregar o app.

### 4. Pre-trip phases e checklist

Checklist:

- Abrir cada fase de pre-trip.
- Ler titulo, subtitulo e descricao.
- Marcar itens de checklist como concluidos.
- Desmarcar um item e marcar novamente.
- Voltar para a home.
- Conferir se a barra/progresso mudou.

Resultado esperado:

- Os checklists respondem sem erro.
- A home reflete o progresso do traveler.
- A fase de ritmo ideal faz sentido para o momento do teste.

### 5. QR Code do traveler

Checklist:

- Abrir **My QR Code**.
- Confirmar que o QR Code aparece.
- Confirmar que o nome/telefone exibido pertence ao traveler correto.
- Pedir para um staff escanear o QR durante o teste de check-in.

Resultado esperado:

- O QR Code aparece sem erro.
- O QR Code pode ser lido pela camera do staff.
- O check-in e registrado na atividade correta.

### 6. Information

Checklist:

- Abrir **Information**.
- Conferir FAQ.
- Conferir recomendacoes locais.
- Conferir contatos e informacoes de emergencia, se visiveis para traveler.
- Abrir o link de recomendacoes locais.
- Validar se os textos estao claros para uma viagem real.

Resultado esperado:

- FAQ aparece em ingles.
- Recomendacoes locais aparecem corretamente.
- Links externos abrem.
- Nenhum conteudo antigo da viagem de teste anterior aparece.

### 7. Mensagens recebidas

Checklist:

- Pedir para um staff enviar uma mensagem com o proprio nome.
- Conferir se a mensagem aparece no lado traveler.
- Pedir para um staff enviar uma mensagem anonima.
- Conferir se a mensagem anonima aparece sem expor o nome do staff.
- Registrar horario de envio e horario de recebimento.

Resultado esperado:

- Mensagens chegam no traveler.
- Mensagem identificada mostra o staff corretamente.
- Mensagem anonima nao mostra o nome do staff.

### 8. Feedback do app

Checklist:

- Abrir a area de feedback.
- Enviar um feedback simples, por exemplo: `Teste de feedback pre-trip`.
- Confirmar que apareceu mensagem de sucesso.
- Fazer outro envio durante o in-trip.

Resultado esperado:

- O feedback e salvo sem erro.
- O traveler recebe confirmacao visual.

## Validacao como staff

Cada pessoa testando como staff deve usar seu telefone de staff e registrar os testes feitos.

### 1. Login e tela inicial de staff

Checklist:

- Entrar no app com telefone de staff.
- Confirmar que abriu a visao de staff.
- Confirmar que a viagem ativa e **Viagem Interna Parrot**.
- Verificar se o roteiro aparece.
- Verificar se os contatos aparecem.
- Verificar se todos os staffs esperados aparecem nas areas operacionais.

Resultado esperado:

- Staff cai direto na tela operacional.
- Staff ve a viagem correta.
- Staff nao precisa entrar como traveler para operar.

### 2. Traveler View

Checklist:

- Usar o botao de alternar para **Traveler View**.
- Conferir a home do traveler.
- Conferir roteiro, perfil, QR Code e informacoes como se fosse viajante.
- Voltar para a visao de staff.

Resultado esperado:

- Staff consegue revisar a experiencia do traveler.
- Staff consegue voltar para a tela operacional.

### 3. Contatos operacionais

Checklist:

- Abrir contatos.
- Conferir accommodation.
- Conferir Parrot Team.
- Conferir emergency contacts, se existirem.
- Conferir nome, funcao e telefone de cada pessoa.

Resultado esperado:

- Contatos aparecem agrupados corretamente.
- Telefones estao visiveis.
- Staffs importantes aparecem para a equipe operacional.

### 4. Mensagens de staff

Checklist:

- Enviar uma mensagem identificada como staff.
- Conferir em um login traveler se a mensagem chegou.
- Enviar uma mensagem anonima.
- Conferir em um login traveler se a mensagem anonima chegou.
- Registrar se houve atraso ou erro.

Resultado esperado:

- Staff consegue enviar comunicados.
- Traveler recebe comunicados.
- Mensagens anonimas nao mostram o nome do staff.

### 5. QR scanner

Checklist:

- Abrir o scanner de QR.
- Selecionar uma atividade inclusa.
- Escanear o QR de um traveler permitido.
- Conferir se o contador da atividade aumentou.
- Tentar escanear o mesmo QR novamente em atividade com limite de 1 check-in.
- Registrar se o app bloqueia duplicidade ou mostra comportamento esperado.

Resultado esperado:

- QR valido e aceito.
- Check-in fica associado a atividade correta.
- Contador muda depois do scan.
- Duplicidade respeita a regra da atividade.

### 6. Atividades inclusas

Checklist:

- Selecionar uma atividade do tipo included.
- Escanear varios travelers.
- Conferir contador antes e depois.
- Conferir se travelers da viagem sao aceitos.

Resultado esperado:

- Atividades inclusas aceitam travelers da viagem.
- O contador mostra progresso real de check-ins.

### 7. Atividades opcionais

Checklist:

- Selecionar uma atividade optional.
- Escanear um traveler que deveria participar.
- Escanear um traveler que nao deveria participar, se a atividade for restrita.
- Conferir se a permissao esta correta.

Resultado esperado:

- Traveler permitido e aceito.
- Traveler nao permitido e bloqueado em atividade restrita.
- O app mostra uma mensagem compreensivel para o staff.

### 8. Atividades restritas

Checklist:

- Abrir uma atividade restrita.
- Confirmar que o total esperado e menor do que o total de travelers da viagem.
- Escanear travelers permitidos.
- Escanear pelo menos um traveler nao permitido.
- Conferir se a lista/contador nao mostra todos os travelers como elegiveis.

Resultado esperado:

- Atividades restritas nao aparecem como `0/total da viagem` quando so parte dos travelers esta autorizada.
- Apenas travelers autorizados conseguem check-in.
- Tentativas recusadas nao contam como check-in valido.

## Validacao in-trip - Dia 1 - 24/08/2026

Foco do dia: confirmar se a viagem mudou corretamente para in-trip e se a operacao de check-in funciona.

Traveler deve validar:

- Home em modo in-trip.
- Roteiro do dia 1.
- Horarios e locais das atividades.
- Progresso do dia.
- Recebimento de mensagens do staff.
- Envio de feedback.
- QR Code disponivel para check-in.

Staff deve validar:

- Atividades do dia 1.
- Check-in em atividade inclusa.
- Check-in em atividade opcional.
- Bloqueio em atividade restrita.
- Contadores de check-in.
- Mensagens para travelers.
- Traveler View durante o dia.

## Validacao in-trip - Dia 2 e periodo estendido - 25/08/2026 a 01/09/2026

Foco: validar atividades finais, opcionais/restritas, feedback final e retestes internos durante a semana adicional.

Traveler deve validar:

- Roteiro do dia 2.
- Detalhes das atividades.
- Recomendacoes locais.
- FAQ.
- Feedback final.
- Progresso final da viagem.

Staff deve validar:

- Check-in das atividades do dia 2.
- Atividade opcional/restrita.
- Travelers autorizados e nao autorizados.
- Limite de check-ins por atividade.
- Contadores finais.
- Consistencia dos contatos operacionais.

## Cenarios de teste obrigatorios

| Cenario | Papel | Resultado esperado |
| --- | --- | --- |
| Traveler faz login | Traveler | Entra na viagem correta |
| Traveler abre My Profile | Traveler | Dados, package e links aparecem corretamente |
| Traveler abre QR Code | Traveler | QR Code aparece e pode ser escaneado |
| Traveler marca checklist | Traveler | Progresso pre-trip muda |
| Traveler envia feedback | Traveler | Feedback e salvo |
| Staff faz login | Staff | Entra na visao operacional |
| Staff alterna para Traveler View | Staff | Consegue revisar experiencia do viajante |
| Staff envia mensagem identificada | Staff + Traveler | Traveler recebe com nome do staff |
| Staff envia mensagem anonima | Staff + Traveler | Traveler recebe sem nome do staff |
| Staff escaneia atividade inclusa | Staff | Check-in aceito |
| Staff escaneia atividade restrita permitida | Staff | Check-in aceito |
| Staff escaneia atividade restrita nao permitida | Staff | Check-in bloqueado |
| Staff escaneia QR duplicado | Staff | App respeita a regra de limite da atividade |
| Staff confere contador | Staff | Numeros batem com check-ins realizados |

## Modelo de registro de evidencias

Use esta tabela para registrar cada teste feito.

| Data | Pessoa testando | Papel | Telefone usado | Funcionalidade | Resultado esperado | Resultado obtido | Status | Link/print | Observacoes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18/08/2026 |  | Traveler |  | Login | Entra na viagem correta |  |  |  |  |
| 18/08/2026 |  | Traveler |  | My Profile | Package e links corretos |  |  |  |  |
| 21/08/2026 |  | Staff |  | Mensagem anonima | Traveler recebe sem nome do staff |  |  |  |  |
| 24/08/2026 |  | Staff |  | QR included | Check-in aceito |  |  |  |  |
| 24/08/2026 |  | Staff |  | QR restrito bloqueado | Traveler nao autorizado e recusado |  |  |  |  |
| 25/08/2026 |  | Traveler |  | Feedback final | Feedback salvo |  |  |  |  |
| 26/08/2026 |  | Traveler/Staff |  | Reteste interno | App continua em modo in-trip |  |  |  |  |

## Bugs e problemas

Quando encontrar problema, registrar:

- Quem testou.
- Telefone usado.
- Tela onde aconteceu.
- Passos para reproduzir.
- Resultado esperado.
- Resultado observado.
- Print ou video.
- Horario aproximado.
- Se aconteceu uma vez ou sempre.

Modelo:

```text
Titulo:
Pessoa:
Papel:
Telefone:
Data/hora:
Tela:
Passos:
Resultado esperado:
Resultado observado:
Print/video:
Observacoes:
```

## Checklist final para considerar a viagem pronta

- Travelers conseguem fazer login.
- Staffs conseguem fazer login.
- Staffs aparecem corretamente na visao operacional.
- My Profile mostra package, add-ons e links corretos.
- QR Codes aparecem para todos os travelers.
- Staff consegue escanear QR Codes.
- Atividades inclusas aceitam check-ins.
- Atividades opcionais funcionam.
- Atividades restritas bloqueiam travelers nao permitidos.
- Contadores de scan fazem sentido.
- Mensagens de staff chegam para travelers.
- Mensagens anonimas preservam anonimato.
- FAQ aparece em ingles.
- Recomendacoes locais abrem corretamente.
- Feedback pode ser enviado.
- Pre-trip funciona entre 18/08/2026 e 23/08/2026.
- In-trip funciona entre 24/08/2026 e 01/09/2026.

## Observacoes importantes

- Este teste deve usar dados ficticios ou usuarios internos.
- Nao usar dados reais de clientes.
- Prints com telefones devem ser compartilhados apenas internamente.
- Se uma atividade for restrita, ela deve ter menos travelers elegiveis do que o total da viagem.
- Se uma mensagem for anonima, o traveler nao deve conseguir identificar o staff que enviou.
- Se algum link antigo aparecer, registrar como bug de conteudo.

# Data Request - Simulacao Real do Aplicativo Parrot Trips

## Contexto

Este documento lista as informacoes necessarias para lancarmos uma viagem real de teste no aplicativo Parrot Trips, usando o casamento dos noivos como ambiente de simulacao.

Os noivos e convidados concordaram em usar o aplicativo para validarmos o funcionamento em um contexto real, observarmos o que gera valor e coletarmos feedbacks antes de escalar para outras viagens.

O objetivo nao e pedir todas as informacoes possiveis. O objetivo e separar claramente:

- **Must Have**: dados sem os quais o aplicativo nao funciona corretamente ou a simulacao perde valor.
- **Nice to Have**: dados que enriquecem a experiencia, mas podem ser adicionados depois.

## Escopo da Simulacao

A simulacao deve cobrir duas camadas:

1. **Experiencia dos convidados/viajantes**
   - Login por WhatsApp com OTP.
   - Visualizacao da viagem/evento.
   - Roteiro por dias e atividades.
   - Perfil individual.
   - QR Code individual para check-in em atividades.
   - Contatos importantes.
   - Comunicados/notificacoes enviados pela equipe.

2. **Operacao da equipe**
   - Visualizacao do roteiro pela equipe.
   - Lista de convidados por atividade.
   - Check-in por QR Code.
   - Contatos operacionais.
   - Envio de comunicados para todos os participantes.

## Principio de Minimizacao de Dados

Devemos coletar apenas os dados necessarios para operar a simulacao.

Alguns dados existem no aplicativo porque fazem sentido para viagens internacionais da Parrot Trips, como passaporte, seguro viagem, tipo de quarto, add-ons pagos e contrato de servico. Para esta simulacao de casamento, esses campos so devem ser pedidos se forem relevantes para o teste.

## 1. Dados Gerais da Viagem/Evento

### Must Have

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Nome da viagem/evento | Aparece no topo do app e identifica a experiencia | Texto curto |
| Destino/local principal | Aparece nos dados da viagem | Cidade, estado/pais ou nome do local |
| Data de inicio | Define viagem ativa e progresso | `YYYY-MM-DD` |
| Data de fim | Define viagem ativa e progresso | `YYYY-MM-DD` |
| Timezone operacional | Evita erro em horarios e check-ins | Ex: `America/Sao_Paulo` |
| Pessoa responsavel pelo envio dos dados | Ponto focal para duvidas | Nome, WhatsApp, email |

### Nice to Have

| Campo | Uso |
|---|---|
| URL publica do evento/casamento | Referencia interna ou link externo |
| Mensagem de boas-vindas | Pode ser usada em comunicacao inicial |
| Imagem/capa do evento | Enriquecimento visual futuro |
| Contrato ou documento de servico | So se quisermos testar a area de Service Agreement |

## 2. Lista de Convidados/Viajantes

### Must Have

Sem esses dados, o login por WhatsApp OTP e o vinculo do convidado com a viagem nao funcionam.

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Nome completo | Identificacao no app, lista da equipe e check-in | Texto |
| Nome preferido/apelido | Como a pessoa aparece no app | Texto, se diferente do nome completo |
| Telefone WhatsApp | Autenticacao OTP e identificacao do convidado | Formato internacional, ex: `+5511999999999` |
| Email | Identificacao complementar e suporte | Email |
| Status do convidado | Evita liberar acesso indevido | `confirmado`, `pendente`, `cancelado` ou equivalente |
| Grupo/categoria | Ajuda operacional | Ex: familia da noiva, familia do noivo, amigos, padrinhos |

### Must Have se houver check-in por atividade

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Atividades em que a pessoa deve participar | Controla presenca esperada por atividade | Nome da atividade ou lista por dia |
| Restricoes de acesso | Evita check-in em atividade restrita | Ex: apenas padrinhos, apenas familia, todos |

### Nice to Have

| Campo | Uso |
|---|---|
| Foto/avatar | Testar visual de perfil |
| Observacoes internas | Suporte da equipe, nao exibido ao convidado |
| Restricoes alimentares | Util se houver refeicoes e para testar perfil |
| Necessidade especial de acessibilidade | Operacao real e cuidado com convidados |
| Acompanhante vinculado | Ajuda a entender grupos e pares |
| Idioma preferido | Futuro suporte a internacionalizacao |

## 3. Equipe/Staff

### Must Have

Sem esses dados, a equipe nao consegue acessar a Staff View nem operar check-ins e comunicados.

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Nome da pessoa da equipe | Identificacao no app | Texto |
| Telefone WhatsApp | Login por OTP da equipe | Formato internacional |
| Funcao | Exibicao para convidados e equipe | Ex: cerimonial, noiva, noivo, producao, Parrot |
| Quais pessoas terao acesso de staff | Controle de permissao | Sim/nao |

### Nice to Have

| Campo | Uso |
|---|---|
| Foto da equipe | Exibicao na secao Parrot Team/Equipe |
| Bio curta | Ajuda convidados a saber quem procurar |
| Responsabilidade por dia/atividade | Permite tarefas operacionais no app |

## 4. Roteiro Dia a Dia

### Must Have

O roteiro e o principal conteudo da experiencia. Sem ele, a Home e os detalhes dos dias ficam vazios.

Para cada dia:

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Numero do dia | Ordenacao no app | `1`, `2`, `3`... |
| Data | Progresso automatico e exibicao | `YYYY-MM-DD` |
| Titulo do dia | Card principal | Ex: `Day 1 - Chegada` |
| Subtitulo | Resumo curto | Uma linha |
| Icone | Visual do mapa da jornada | Ex: `plane-landing`, `sun`, `bus`, `palmtree`, `landmark` |
| Descricao curta | Aparece na listagem | Uma frase |
| Descricao completa | Aparece ao abrir o dia | 1 a 3 paragrafos |

Para cada atividade:

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Nome da atividade | Identificacao no roteiro e staff view | Texto curto |
| Tipo da atividade | Define label visual | `included`, `optional`, `suggested`, `logistics` |
| Horario de inicio | Ordenacao e operacao | `HH:MM` |
| Duracao estimada | Exibicao e planejamento | Minutos |
| Descricao curta | Texto principal do card | Uma frase |
| Informacoes praticas | Orientacao para convidados | Ponto de encontro, roupa, documentos, observacoes |
| Endereco | Link de mapa na Staff View | Endereco completo ou link de referencia |
| Maximo de scans por pessoa | Controle de presenca | Normalmente `1`; usar `2+` se houver entrada e saida |

### Nice to Have

| Campo | Uso |
|---|---|
| Preco | Apenas para atividade opcional |
| Link externo | Reserva, mapa, site do local |
| Foto da atividade/local | Enriquecimento visual futuro |
| Dress code estruturado | Pode entrar em informacoes praticas |
| Plano B em caso de chuva | Pode entrar em informacoes praticas ou FAQ |

## 5. Fases Pre-Evento / Preparacao

O app possui fases pre-trip com checklist. Para casamento, podemos adaptar as fases para preparacao do evento.

### Must Have

Recomendacao: usar poucas fases, apenas se quisermos testar progresso antes do evento.

| Campo | Por que precisamos | Exemplo |
|---|---|---|
| Titulo da fase | Card da Home | `Confirmar Presenca` |
| Subtitulo | Resumo | `RSVP e dados basicos` |
| Descricao curta | Card | `Finalize sua confirmacao antes do evento` |
| Descricao completa | Tela de detalhes | Explicacao do que precisa ser feito |
| Checklist | Progresso individual | `Confirmar presenca`, `Informar restricoes alimentares` |
| Links uteis | Acesso rapido | Site do casamento, mapa, lista de presentes |

### Nice to Have

| Campo | Uso |
|---|---|
| Ideal pace | Mostra onde o convidado deveria estar no progresso |
| Fases adicionais | Ex: traje, transporte, hospedagem |

## 6. Contatos Importantes

### Must Have

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Nome do contato | Exibicao no app | Texto |
| Categoria | Agrupamento na Staff View | Ex: emergencia, cerimonial, transporte, local |
| Funcao/cargo | Ajuda contexto | Texto |
| Telefone | Clique para ligar ou WhatsApp | Formato internacional quando possivel |

### Nice to Have

| Campo | Uso |
|---|---|
| Horario de disponibilidade | Evita contato fora do periodo correto |
| Observacao de uso | Ex: "usar apenas em emergencia" |

## 7. FAQ

### Must Have

FAQ nao e tecnicamente obrigatorio para o app funcionar, mas e recomendado para reduzir duvidas durante uma simulacao real.

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Pergunta | Exibida na secao Information | Texto |
| Resposta | Exibida ao abrir a pergunta | Texto |
| Ordem | Organizacao | Numero |

Perguntas recomendadas:

- Qual e o dress code?
- Onde estacionar?
- Qual e o horario limite de chegada?
- Havera transporte?
- Posso levar acompanhante?
- O que fazer em caso de atraso?
- Quem devo chamar em caso de problema?

### Nice to Have

| Campo | Uso |
|---|---|
| FAQ por grupo de convidado | Ex: padrinhos vs convidados gerais |
| Links externos nas respostas | Site do casamento, mapa, hospedagem |

## 8. Recomendacoes Locais

### Nice to Have

Nao e necessario para a simulacao funcionar, mas ajuda a testar a secao de informacoes e pode gerar valor real para convidados de fora.

| Campo | Uso |
|---|---|
| Nome do local | Restaurante, bar, hotel, salao, ponto turistico |
| Descricao | Por que recomendamos |
| Endereco | Link para mapa |
| Foto URL | Imagem exibida no app |
| Ordem | Organizacao |

## 9. Politica de Cancelamento / Regras do Evento

### Nice to Have

Para casamento, a secao pode ser adaptada para "Regras e Informacoes Importantes", caso a politica de cancelamento nao faca sentido.

| Campo | Uso |
|---|---|
| Titulo | Ex: `Confirmacao de presenca` |
| Texto | Regra ou orientacao |
| Ordem | Organizacao |

## 10. Comunicados / Notificacoes

### Must Have para testar notificacoes

O app permite que staff envie comunicados para todos os participantes. Para a simulacao, precisamos definir quem pode enviar e quais mensagens devem ser testadas.

| Campo | Por que precisamos | Exemplo |
|---|---|---|
| Pessoas autorizadas a enviar | Evita comunicados indevidos | Cerimonial, Parrot, noivos |
| Mensagens de teste planejadas | Valida fluxo sem improviso | `O ponto de encontro mudou para a entrada principal` |
| Janela de envio | Evita incomodar convidados fora do teste | Durante o evento ou ensaio |

### Nice to Have

| Campo | Uso |
|---|---|
| Biblioteca de mensagens prontas | Agiliza operacao |
| Comunicados anonimos | Testar envio sem nome do remetente |

## 11. Check-in por QR Code

### Must Have se a simulacao incluir controle de presenca

| Campo | Por que precisamos | Formato esperado |
|---|---|---|
| Quais atividades terao check-in | Define onde usar QR | Lista de atividades |
| Quem pode fazer check-in em cada atividade | Define lista esperada | Todos ou lista especifica |
| Quantos scans por pessoa | Controle de entrada/saida | `1`, `2` etc. |
| Quem sera staff scanner | Permissao operacional | Nome e telefone |

### Nice to Have

| Campo | Uso |
|---|---|
| Criterio de sucesso do check-in | Ex: 95% dos convidados escaneados |
| Plano de contingencia | Busca manual por nome se camera falhar |
| Atividades controladas por grupo | Ex: apenas padrinhos no ensaio |

## 12. Perfil do Convidado

### Must Have

Para esta simulacao, o minimo de perfil deve ser:

| Campo | Por que precisamos |
|---|---|
| Nome preferido | Exibicao no app |
| Email | Suporte e identificacao |
| Telefone | Login e vinculo |

### Nice to Have

Campos ja suportados pelo app, mas que so devem ser pedidos se fizerem sentido:

| Campo | Quando pedir |
|---|---|
| Data de nascimento | Se houver validacao de idade ou teste de formulario |
| Genero | Se for util para operacao ou teste |
| Restricoes alimentares | Se houver refeicoes |
| Enjoo em barco | Se houver passeio de barco |
| Acompanhante | Se houver controle de plus one |
| Ajuda com voo | Normalmente nao necessario para casamento local |
| Ajuda com seguro viagem | Normalmente nao necessario para casamento |
| O que tornaria a experiencia inesquecivel | Bom para feedback qualitativo |
| Foto/avatar | Bom para testar personalizacao |

Campos de passaporte, seguro viagem internacional, pacote, quarto, add-ons pagos e contrato de servico nao devem ser pedidos para esta simulacao, salvo se decidirmos testar essas secoes especificamente.

## 13. Formato de Entrega Recomendado

### Planilha 1 - Convidados

Colunas sugeridas:

```text
nome_completo
nome_preferido
telefone_whatsapp
email
status
grupo
restricoes_alimentares
acompanhante_nome
observacoes
```

### Planilha 2 - Roteiro

Colunas sugeridas, alinhadas ao import atual:

```text
trip_uuid
dia
data
dia_titulo
dia_subtitulo
dia_icon
dia_descricao_curta
dia_descricao_completa
atividade_nome
atividade_tipo
atividade_horario
atividade_duracao_min
atividade_descricao_curta
atividade_info_pratica
atividade_endereco
atividade_max_scans
atividade_preco_brl
```

### Planilha 3 - Staff e Contatos

Colunas para equipe:

```text
trip_uuid
phone
nome
funcao
photo_url
bio
```

Colunas para contatos:

```text
trip_uuid
category
name
role
phone
sort_order
```

### Planilha 4 - Participantes por Atividade

Necessaria apenas para atividades controladas.

```text
trip_uuid
dia
atividade_nome
traveler_phone
status
```

Valor esperado para `status`: `allowed`.

### Planilha 5 - Tarefas de Staff

Necessaria apenas se quisermos testar tarefas operacionais no app.

```text
trip_uuid
dia
atividade_nome
staff_phone
titulo
descricao
sort_order
```

### Planilha 6 - FAQ / Regras / Recomendacoes

FAQ:

```text
trip_uuid
question
answer
sort_order
```

Regras ou politica:

```text
trip_uuid
title
body
sort_order
```

Recomendacoes:

```text
trip_uuid
name
description
address
photo_url
sort_order
```

## 14. Checklist de Pronto para Lancar

Antes de liberar o app para os noivos/convidados, precisamos confirmar:

- Todos os convidados que devem acessar o app tem telefone WhatsApp em formato internacional.
- Todos os telefones foram autorizados no sistema.
- Todos os convidados confirmados estao vinculados a viagem.
- Pelo menos um usuario staff consegue logar.
- A viagem aparece corretamente apos login.
- O roteiro tem pelo menos um dia e uma atividade.
- As atividades que terao check-in tem `atividade_max_scans` definido.
- A equipe sabe quem fara os scans por QR.
- Os contatos essenciais estao cadastrados.
- Uma mensagem de teste foi combinada para validar notificacoes.
- O plano de feedback esta definido.

## 15. Feedbacks que Queremos Coletar

Durante e depois da simulacao, devemos observar:

- Os convidados conseguem logar sem ajuda?
- O OTP por WhatsApp chega rapido?
- O roteiro e facil de entender?
- Os convidados abrem os detalhes das atividades?
- O QR Code e facil de encontrar no perfil?
- A equipe consegue escanear QR Codes sem friccao?
- A busca manual por nome funciona como contingencia?
- As notificacoes sao percebidas pelos convidados?
- As informacoes de contato reduzem perguntas para os noivos/equipe?
- Quais secoes foram ignoradas?
- Quais informacoes os convidados esperavam encontrar e nao encontraram?

## 16. Responsabilidades

| Responsavel | Papel |
|---|---|
| Noivos / organizacao do casamento | Fornecer lista de convidados, roteiro real, contatos e regras |
| Parrot Trips | Preparar banco, importar dados, liberar acessos e monitorar teste |
| Staff do evento | Usar Staff View, fazer check-ins e enviar comunicados combinados |
| Convidados | Usar o app durante a simulacao e enviar feedback |

## 17. Resumo Executivo

Para lancar a viagem, o minimo necessario e:

- Dados gerais do evento.
- Lista de convidados com nome, telefone WhatsApp e email.
- Roteiro com dias e atividades.
- Pelo menos um staff autorizado.
- Contatos essenciais.
- Definicao clara de quais atividades terao check-in por QR.

Todo o restante, como recomendacoes locais, FAQ completa, fotos, bios, tarefas detalhadas e regras adicionais, melhora a simulacao, mas nao deve bloquear o lancamento.

# Guia de Apresentação — App do Viajante

Apresentação ao vivo para o time de operação.
Objetivo: validar que está funcionando e treinar quem vai operar.
Tempo estimado: 30 minutos.

---

## Antes de começar

Tenha aberto no computador ou celular:
- App: https://parrot-trips.netlify.app
- Planilha de conteúdo da viagem (Google Sheets)
- WhatsApp do número de teste do viajante

---

## Bloco 1 — App do viajante (20 min)

### 1.1 Login

1. Abrir https://parrot-trips.netlify.app no celular.
2. Digitar o telefone do viajante de teste.
3. Clicar em enviar código.
4. Abrir o WhatsApp e mostrar o código chegando.
5. Digitar o código e entrar.

**Mensagem para o time:**

> "Temos um banco de dados que recebe os dados assim que um novo viajante compra uma viagem. No momento da compra, já salvamos automaticamente o telefone, o nome, o email, o pacote comprado, os add-ons e o valor pago. Por isso o viajante já consegue entrar aqui sem nenhum cadastro manual."

**O que confirmar:** app abre na viagem correta, nome do viajante aparece.

---

### 1.2 Pré-trip (Home)

1. Mostrar as fases que aparecem na tela inicial.
2. Abrir uma fase (ex: "Documentos").
3. Mostrar o checklist de tarefas dentro da fase.
4. Marcar um item do checklist.
5. Mostrar que o progresso da fase atualiza.
6. Mostrar os links dentro da fase se houver.
7. Voltar e mostrar a barra de progresso geral.

**Mensagem para o time:**

> "Todo esse conteúdo — fases, tarefas, links — vem da planilha. A operação controla o que o viajante vê aqui."

---

### 1.3 In-trip (Roteiro)

1. Navegar para a aba de roteiro.
2. Mostrar o dia atual (ou o dia simulado da viagem de teste).
3. Abrir uma atividade do dia.
4. Mostrar a descrição da atividade.
5. Mostrar a informação prática.
6. Mostrar links se houver.

**Mensagem para o time:**

> "Dia, descrição e informações práticas — tudo vem da planilha também."

---

### 1.4 Profile — Registration Details

1. Abrir a aba Profile.
2. Entrar em Registration Details.
3. Mostrar os campos Basic Info:
   - Preferred Name → vem da WeTravel como base, viajante pode ajustar
   - Email → vem da WeTravel como base, viajante pode ajustar
   - Date of Birth, Gender → preenchidos pelo viajante
4. Mostrar os campos de passaporte.
5. Mostrar os campos de saúde, dieta e informações adicionais.
6. Preencher alguns campos ao vivo.
7. Clicar em Save Profile.
8. Mostrar a confirmação de sucesso.
9. Recarregar o app e mostrar que os dados persistiram.

**Mensagem para o time:**

> "Ao clicar em Save Profile, todas as informações alteradas aqui vão para o nosso banco de dados e ficam atualizadas no aplicativo. O nome e o email já chegam da WeTravel como ponto de partida — o restante o próprio viajante preenche."

---

### 1.5 Profile — Products & Payment

1. Ainda no Profile, abrir Products & Payment.
2. Mostrar o bloco YOUR PACKAGE:
   - Package Name → vem da WeTravel
   - Amount Paid → vem da WeTravel
3. Mostrar o bloco ADDITIONAL ACTIVITIES PURCHASED:
   - Add-on Activities → vem da WeTravel

**Mensagem para o time:**

> "Essas informações também vêm diretamente da WeTravel. O pacote, o valor pago e os add-ons são exatamente o que o viajante comprou lá — sem nenhuma digitação manual."

---

### 1.6 Profile — Service Agreement

1. Ainda no Profile, abrir Service Agreement.
2. Clicar em View Service Agreement.
3. Mostrar o PDF abrindo.

**Mensagem para o time:**

> "O contrato é um documento anexado através da planilha. Ele é único por viagem — então cada viagem tem o seu próprio PDF. O viajante pode verificar aqui o contrato relacionado ao que comprou."

---

### 1.7 QR Code

1. Navegar para a aba QR Code.
2. Mostrar o QR Code do viajante na tela.

**Mensagem para o time:**

> "Esse código identifica o viajante. Na parte do staff, veremos como escanear para registrar presença em cada atividade."

---

## Bloco 2 — Planilha + botões de import (10 min)

### 2.1 Estrutura da planilha

Mostrar as abas da planilha:

| Aba | O que contém |
|---|---|
| Viagens | trip_uuid, nome, datas, link do service agreement |
| Fases | Fases do pré-trip com título, subtítulo e descrição |
| Checklist | Tarefas por fase |
| Links | Links por fase |
| Roteiro | Dias, atividades, descrições, informações práticas |

**Mensagem para o time:**

> "Essa planilha é o painel de controle do conteúdo da viagem. O que está aqui é o que o viajante vê no app."

---

### 2.2 Menu Parrot no topo da planilha

Mostrar o menu Parrot que aparece na barra superior da planilha:

| Botão | O que faz |
|---|---|
| 🔄 Sync Trips from Supabase | Atualiza a aba Viagens com as viagens cadastradas no sistema |
| Import Trip Content → Supabase | Envia o conteúdo das abas para o app (fases, checklist, links, roteiro) |
| 🚀 Iniciar Viagem → In-Trip | Muda o status da viagem de pré-trip para in-trip |
| 🔁 Reset Trip → Pre-Trip | Volta a viagem para pré-trip (útil em testes) |
| 🔧 Setup Sheet Headers | Cria as abas e cabeçalhos automaticamente (só precisa rodar uma vez) |

---

### 2.3 Import ao vivo

1. Fazer uma pequena alteração na planilha (ex: mudar o texto de uma fase ou adicionar um item de checklist).
2. Clicar em **Import Trip Content → Supabase**.
3. Aguardar a confirmação de sucesso.
4. Abrir o app do viajante e mostrar o conteúdo atualizado.

**Mensagem para o time:**

> "É assim que a operação atualiza o app. Edita na planilha, clica em importar, e em segundos o viajante já vê a mudança."

---

## Resumo para o time

| Fonte | O que ela controla |
|---|---|
| WeTravel | Acesso ao app, nome, email, pacote, add-ons, valor pago |
| Planilha | Roteiro, fases, checklist, links, service agreement |
| Viajante no app | Dados pessoais complementares e passaporte |

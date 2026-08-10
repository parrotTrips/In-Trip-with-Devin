# Viagem Teste - Simulacao Completa Parrot Trips

Este arquivo descreve um dataset completo para validar tudo que existe hoje no app da Parrot Trips em uma simulacao realista:

- 3 fases pre-trip;
- 2 dias in-trip;
- varias atividades por dia;
- atividades restritas/controladas;
- todos da Parrot como staff;
- perfis de viajantes preenchidos;
- QR Codes a serem criados para simulacao;
- contatos, equipe, FAQ, recomendacoes, politica/regras, tarefas de staff e notificacoes.

Os dados pessoais abaixo sao ficticios. Informacoes turisticas e emergenciais foram baseadas em referencias publicas listadas no final do arquivo.

---

## 1. Identificacao da viagem

### Registro base da viagem

| campo | valor |
|---|---|
| trip_uuid | `PARROT-RIO-FULL-TEST-2026` |
| title | `Parrot Rio Full App Simulation` |
| destination | `Rio de Janeiro, Brazil` |
| start_date | `2026-09-18` |
| end_date | `2026-09-19` |
| url | `https://parrottrips.com/test/parrot-rio-full-app-simulation` |
| service_agreement_url | `https://parrottrips.com/test/service-agreement-parrot-rio-full-app-simulation.pdf` |
| timezone | `America/Sao_Paulo` |
| trip_mode inicial | `pre-trip` |
| trip_mode para simulacao in-trip | mudar para `in-trip` no dia do teste operacional |
| ideal_pace_phase | `pretrip_checklist_operacional` |

### Objetivo do teste

Validar o ciclo completo do app:

- login via WhatsApp OTP;
- Home/jogo da vida;
- progresso pre-trip;
- virada para in-trip;
- detalhes de dias e atividades;
- perfil completo;
- pacotes e add-ons;
- QR Code individual;
- check-in por QR;
- atividades restritas;
- staff view;
- contatos operacionais;
- tarefas de staff;
- envio e leitura de notificacoes;
- informacoes gerais;
- FAQ;
- recomendacoes locais;
- politica/regras.

---

## 2. Abas/entidades que devem ser preenchidas

Para esta simulacao, preencher todas as entidades abaixo:

| entidade | obrigatorio para o teste completo | observacao |
|---|---:|---|
| `wetravel_trips` / aba Viagens | sim | viagem ativa e contrato |
| `users` | sim | viajantes e staff |
| `trip_travelers` | sim | vinculo usuario-viagem |
| `traveler_profiles` | sim | perfil completo |
| `traveler_products` / dados WeTravel equivalentes | sim | pacote, quarto e add-ons |
| `trip_settings` | sim | modo pre-trip/in-trip e ideal pace |
| `trip_phases` | sim | 3 pre-trip + 2 in-trip |
| `trip_phase_checklist_items` | sim | checklist de fases pre-trip |
| `trip_phase_links` | sim | links uteis por fase |
| `trip_activities` | sim | atividades dos 2 dias |
| `activity_participants` | sim | atividades restritas |
| `activity_checkins` | sim durante teste | gerado por scan |
| `activity_checkin_scan_events` | sim durante teste | auditoria de scans |
| `trip_staff` | sim | todos da Parrot como staff |
| `staff_tasks` | sim | tarefas por atividade |
| `trip_contacts` | sim | contatos para staff |
| `trip_emergency_contacts` | sim | contatos para viajante |
| `trip_recommendations` | sim | dicas locais |
| `trip_faqs` | sim | FAQ completo |
| `trip_cancellation_policies` | sim | usar como regras do teste |
| `trip_announcements` | sim durante teste | notificacoes enviadas pelo staff |

---

## 3. Usuarios viajantes

Telefones ficticios em formato internacional. Substituir por telefones reais apenas no ambiente controlado.

| role | full_name | preferred_name | phone | email | status | grupo |
|---|---|---|---|---|---|---|
| traveler | Ana Martins | Ana | `+15550001001` | `ana.martins@example.com` | active | founders |
| traveler | Bruno Lee | Bruno | `+15550001002` | `bruno.lee@example.com` | active | founders |
| traveler | Camila Rocha | Camila | `+15550001003` | `camila.rocha@example.com` | active | operations |
| traveler | Daniel Kim | Daniel | `+15550001004` | `daniel.kim@example.com` | active | operations |
| traveler | Elena Costa | Elena | `+15550001005` | `elena.costa@example.com` | active | guests |
| traveler | Felipe Santos | Felipe | `+15550001006` | `felipe.santos@example.com` | active | guests |
| traveler | Gabriela Torres | Gabi | `+15550001007` | `gabriela.torres@example.com` | active | guests |
| traveler | Hugo Almeida | Hugo | `+15550001008` | `hugo.almeida@example.com` | active | guests |

### Perfis completos para validar ProfileScreen

| phone | dob | gender | passport_first_name | passport_last_name | passport_country | passport_number | passport_issue_date | passport_expiration_date | dietary_restrictions_yn | dietary_restrictions_desc | seasickness_yn | plus_one_yn | plus_one_name | plus_one_email | intl_flights_help_yn | intl_flights_help_details | travel_insurance_help_yn | unforgettable_trip_details | avatar_url |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `+15550001001` | `1991-04-12` | female | Ana | Martins | United States | X1001001 | `2022-01-10` | `2032-01-09` | yes | Vegetarian, no seafood | no | no |  |  | no |  | yes | Sunrise view and local music | `https://example.com/avatars/ana.jpg` |
| `+15550001002` | `1989-08-03` | male | Bruno | Lee | Canada | X1001002 | `2021-06-20` | `2031-06-19` | no |  | yes | yes | Nina Park | `nina.park@example.com` | no |  | no | Smooth logistics and good food | `https://example.com/avatars/bruno.jpg` |
| `+15550001003` | `1994-11-21` | female | Camila | Rocha | Brazil | X1001003 | `2020-03-15` | `2030-03-14` | yes | Gluten-free | no | no |  |  | yes | Wants help changing return flight | yes | Meet local operators | `https://example.com/avatars/camila.jpg` |
| `+15550001004` | `1990-02-18` | male | Daniel | Kim | United States | X1001004 | `2023-05-01` | `2033-04-30` | no |  | no | no |  |  | no |  | yes | Test every QR flow | `https://example.com/avatars/daniel.jpg` |
| `+15550001005` | `1996-07-09` | non-binary | Elena | Costa | Portugal | X1001005 | `2019-09-10` | `2029-09-09` | yes | Lactose intolerance | yes | no |  |  | no |  | yes | Better recommendations | `https://example.com/avatars/elena.jpg` |
| `+15550001006` | `1987-12-29` | male | Felipe | Santos | Brazil | X1001006 | `2024-02-02` | `2034-02-01` | no |  | no | yes | Paula Reis | `paula.reis@example.com` | no |  | no | Operational clarity | `https://example.com/avatars/felipe.jpg` |
| `+15550001007` | `1993-03-30` | female | Gabriela | Torres | Mexico | X1001007 | `2022-10-05` | `2032-10-04` | yes | Nut allergy | no | no |  |  | yes | Arrives late, needs airport help | yes | Safety info in app | `https://example.com/avatars/gabi.jpg` |
| `+15550001008` | `1992-06-14` | male | Hugo | Almeida | Spain | X1001008 | `2021-12-11` | `2031-12-10` | no |  | yes | no |  |  | no |  | yes | Boat day without confusion | `https://example.com/avatars/hugo.jpg` |

### Pacotes e add-ons para validar Packages

| phone | package_option | room_type | num_people | paid_amount_usd | addon_names |
|---|---|---:|---:|---:|---|
| `+15550001001` | Rio Test Package | Single Room | 1 | 1250 | Sunset Boat Add-on |
| `+15550001002` | Rio Test Package | Double Room | 2 | 2200 | Sunset Boat Add-on, Samba Night |
| `+15550001003` | Rio Test Package | Twin Shared Room | 1 | 1100 | Staff Shadow Add-on |
| `+15550001004` | Rio Test Package | Twin Shared Room | 1 | 1100 | QR Ops Add-on |
| `+15550001005` | Rio Test Package | Single Room | 1 | 1250 | Local Food Add-on |
| `+15550001006` | Rio Test Package | Double Room | 2 | 2200 | None |
| `+15550001007` | Rio Test Package | Single Room | 1 | 1250 | Airport Fast Track |
| `+15550001008` | Rio Test Package | Twin Shared Room | 1 | 1100 | Boat Add-on |

---

## 4. Staff Parrot

Todos da Parrot devem ser cadastrados como `role = staff`, vinculados a `PARROT-RIO-FULL-TEST-2026` em `trip_travelers` e em `trip_staff`.

| phone | nome | funcao | photo_url | bio |
|---|---|---|---|---|
| `+15550002001` | Marcelo Fazio | Product / Trip Lead | `https://example.com/staff/marcelo.jpg` | Lidera a simulacao, valida UX e operacao. |
| `+15550002002` | Ana Parrot | Traveler Support | `https://example.com/staff/ana-parrot.jpg` | Responsavel por suporte aos viajantes e comunicados. |
| `+15550002003` | Bruno Parrot | Operations Lead | `https://example.com/staff/bruno-parrot.jpg` | Coordena check-ins, horarios e fornecedores. |
| `+15550002004` | Clara Parrot | Content Manager | `https://example.com/staff/clara-parrot.jpg` | Valida roteiro, FAQ, recomendacoes e textos no app. |
| `+15550002005` | Diego Parrot | QR Scanner | `https://example.com/staff/diego-parrot.jpg` | Opera scanner QR e casos de contingencia. |
| `+15550002006` | Elisa Parrot | Emergency Contact | `https://example.com/staff/elisa-parrot.jpg` | Ponto focal de saude, seguranca e emergencias. |

---

## 5. Trip settings

| trip_uuid | mode | ideal_pace_phase_id |
|---|---|---|
| `PARROT-RIO-FULL-TEST-2026` | `pre-trip` | id da fase `pretrip_checklist_operacional` apos import |

Durante o teste:

1. Rodar primeiro em `pre-trip`.
2. Validar progresso manual das 3 fases.
3. Resetar progresso se necessario.
4. Mudar para `in-trip`.
5. Validar progresso automatico dos 2 dias por `starts_at`.

---

## 6. Fases pre-trip - aba Fases

Esta simulacao usa 3 fases pre-trip. No import atual, essas fases entram como linhas da aba `Fases`.

| trip_uuid | ordem | fase | titulo | subtitulo | icone | descricao_curta | descricao_completa | ideal_pace |
|---|---:|---|---|---|---|---|---|---|
| `PARROT-RIO-FULL-TEST-2026` | 1 | `pretrip_documentos` | Documents & Access | Passport, app login and service agreement | `passport` | Confirm your access and travel basics before the test. | Use this phase to validate app login, service agreement visibility, passport fields and traveler identity data. |  |
| `PARROT-RIO-FULL-TEST-2026` | 2 | `pretrip_checklist_operacional` | Operational Checklist | Health, dietary, QR and profile completion | `file-text` | Complete the information needed for operations and QR check-in. | This is the ideal pace phase for the simulation. Travelers should complete profile, dietary restrictions, seasickness answer and QR readiness before the in-trip mode starts. | `yes` |
| `PARROT-RIO-FULL-TEST-2026` | 3 | `pretrip_rio_ready` | Rio Ready | Safety, weather, packing and arrival logistics | `luggage` | Review Rio logistics, emergency numbers and what to bring. | This phase validates travel guidance, useful links, practical reminders and final preparation before the live itinerary. |  |

---

## 7. Checklist pre-trip - aba Checklist

| trip_uuid | fase | ordem | label | obrigatorio |
|---|---|---:|---|---|
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_documentos` | 1 | Log in with WhatsApp OTP | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_documentos` | 2 | Open and verify Service Agreement | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_documentos` | 3 | Confirm passport fields in profile | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_documentos` | 4 | Confirm email and preferred name | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_checklist_operacional` | 1 | Fill dietary restrictions | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_checklist_operacional` | 2 | Fill seasickness answer | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_checklist_operacional` | 3 | Open My QR Code section | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_checklist_operacional` | 4 | Confirm add-ons shown correctly | false |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_rio_ready` | 1 | Save Parrot emergency contact | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_rio_ready` | 2 | Review Rio emergency numbers | true |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_rio_ready` | 3 | Review airport arrival instructions | false |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_rio_ready` | 4 | Pack sunscreen, ID and light rain jacket | false |

---

## 8. Links pre-trip - aba Links

| trip_uuid | fase | ordem | label | url |
|---|---|---:|---|---|
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_documentos` | 1 | Parrot test service agreement | `https://parrottrips.com/test/service-agreement-parrot-rio-full-app-simulation.pdf` |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_documentos` | 2 | Brazil travel information - U.S. State Department | `https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Brazil.html` |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_checklist_operacional` | 1 | Rio tourist information - Riotur | `https://riotur.rio/en/secao/tourist-information/` |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_rio_ready` | 1 | Rio useful emergency numbers | `https://www.riocomsaude.rj.gov.br/hotsite/english/telefonesuteis.php` |
| `PARROT-RIO-FULL-TEST-2026` | `pretrip_rio_ready` | 2 | SAMU 192 - Ministerio da Saude | `https://www.gov.br/saude/pt-br/composicao/saes/samu-192` |

---

## 9. Roteiro in-trip - aba Roteiro

Tipos aceitos pelo frontend:

- `included`
- `optional`
- `suggested`
- `logistics`

### Dia 1 - Rio arrival, operations and icons

| trip_uuid | dia | data | dia_titulo | dia_subtitulo | dia_icon | dia_descricao_curta | dia_descricao_completa | atividade_nome | atividade_tipo | atividade_horario | atividade_duracao_min | atividade_descricao_curta | atividade_info_pratica | atividade_endereco | atividade_max_scans | atividade_preco_brl |
|---|---:|---|---|---|---|---|---|---|---|---|---:|---|---|---|---:|---:|
| `PARROT-RIO-FULL-TEST-2026` | 1 | `2026-09-18` | Day 1 - Arrival & Rio Icons | Airport, hotel, Selaron and Sugarloaf | `plane-landing` | Validate arrival logistics, public itinerary, restricted check-ins and staff tasks. | First operational simulation day in Rio. Travelers arrive, check in at the hotel, test QR at an internal briefing, visit the Selaron/Lapa area and finish with sunset at Sugarloaf. | Airport pickup - Santos Dumont | logistics | `09:00` | 90 | Staff receives travelers and validates late-arrival support. | Meeting point at arrivals. Staff must manually check Ana and Bruno if camera fails. | `Praca Senador Salgado Filho, s/n - Centro, Rio de Janeiro - RJ` | 1 |  |
| `PARROT-RIO-FULL-TEST-2026` | 1 | `2026-09-18` | Day 1 - Arrival & Rio Icons | Airport, hotel, Selaron and Sugarloaf | `plane-landing` | Validate arrival logistics, public itinerary, restricted check-ins and staff tasks. | First operational simulation day in Rio. Travelers arrive, check in at the hotel, test QR at an internal briefing, visit the Selaron/Lapa area and finish with sunset at Sugarloaf. | Hotel check-in and profile audit | logistics | `11:00` | 60 | Validate profile fields, package info and QR section on traveler phones. | Staff asks each traveler to open My Profile, show package and show QR Code. | `Copacabana, Rio de Janeiro - RJ` | 1 |  |
| `PARROT-RIO-FULL-TEST-2026` | 1 | `2026-09-18` | Day 1 - Arrival & Rio Icons | Airport, hotel, Selaron and Sugarloaf | `plane-landing` | Validate arrival logistics, public itinerary, restricted check-ins and staff tasks. | First operational simulation day in Rio. Travelers arrive, check in at the hotel, test QR at an internal briefing, visit the Selaron/Lapa area and finish with sunset at Sugarloaf. | Internal Parrot Ops Briefing | included | `12:30` | 75 | Restricted activity for founders and operations group only. | Controlled check-in. Only Ana, Bruno, Camila and Daniel should be allowed. Use this to validate denied QR for non-participants. | `Copacabana, Rio de Janeiro - RJ` | 2 |  |
| `PARROT-RIO-FULL-TEST-2026` | 1 | `2026-09-18` | Day 1 - Arrival & Rio Icons | Airport, hotel, Selaron and Sugarloaf | `plane-landing` | Validate arrival logistics, public itinerary, restricted check-ins and staff tasks. | First operational simulation day in Rio. Travelers arrive, check in at the hotel, test QR at an internal briefing, visit the Selaron/Lapa area and finish with sunset at Sugarloaf. | Escadaria Selaron Photo Stop | suggested | `15:00` | 60 | Suggested cultural/photo stop in Lapa. | Good for testing suggested activity label. Tell travelers to keep valuables secure and stay with the group. | `Rua Manuel Carneiro, Santa Teresa, Rio de Janeiro - RJ` | 1 |  |
| `PARROT-RIO-FULL-TEST-2026` | 1 | `2026-09-18` | Day 1 - Arrival & Rio Icons | Airport, hotel, Selaron and Sugarloaf | `plane-landing` | Validate arrival logistics, public itinerary, restricted check-ins and staff tasks. | First operational simulation day in Rio. Travelers arrive, check in at the hotel, test QR at an internal briefing, visit the Selaron/Lapa area and finish with sunset at Sugarloaf. | Sugarloaf Sunset Test | optional | `17:00` | 150 | Optional sunset visit using public tourist information as context. | Controlled optional check-in. Only travelers with Sugarloaf/Sunset add-on should be allowed. Confirm address and map link in staff view. | `Avenida Pasteur, 520 - Urca, Rio de Janeiro - RJ` | 1 | 180 |
| `PARROT-RIO-FULL-TEST-2026` | 1 | `2026-09-18` | Day 1 - Arrival & Rio Icons | Airport, hotel, Selaron and Sugarloaf | `plane-landing` | Validate arrival logistics, public itinerary, restricted check-ins and staff tasks. | First operational simulation day in Rio. Travelers arrive, check in at the hotel, test QR at an internal briefing, visit the Selaron/Lapa area and finish with sunset at Sugarloaf. | Anonymous notification drill | logistics | `20:00` | 20 | Staff sends one anonymous operational announcement. | Message: Tomorrow departure moved to 08:15. Validate Notifications tab on traveler phones. | `Copacabana, Rio de Janeiro - RJ` | 1 |  |

### Dia 2 - Christ, boat and closing simulation

| trip_uuid | dia | data | dia_titulo | dia_subtitulo | dia_icon | dia_descricao_curta | dia_descricao_completa | atividade_nome | atividade_tipo | atividade_horario | atividade_duracao_min | atividade_descricao_curta | atividade_info_pratica | atividade_endereco | atividade_max_scans | atividade_preco_brl |
|---|---:|---|---|---|---|---|---|---|---|---|---:|---|---|---|---:|---:|
| `PARROT-RIO-FULL-TEST-2026` | 2 | `2026-09-19` | Day 2 - Corcovado, Boat & Wrap-up | Christ the Redeemer, controlled boat check-in and final feedback | `sun` | Validate in-trip progress, multiple scans, restrictions and feedback workflow. | Second operational simulation day. The group tests date-driven progress, controlled access, multiple QR scans and final feedback collection. | Corcovado early departure | logistics | `08:15` | 45 | Departure from hotel to Christ the Redeemer access point. | Ask travelers to open Day 2 in app and confirm today's itinerary. | `Copacabana, Rio de Janeiro - RJ` | 1 |  |
| `PARROT-RIO-FULL-TEST-2026` | 2 | `2026-09-19` | Day 2 - Corcovado, Boat & Wrap-up | Christ the Redeemer, controlled boat check-in and final feedback | `sun` | Validate in-trip progress, multiple scans, restrictions and feedback workflow. | Second operational simulation day. The group tests date-driven progress, controlled access, multiple QR scans and final feedback collection. | Christ the Redeemer Visit | included | `09:30` | 120 | Included visit to Rio's main landmark. | Use public info that the monument is generally visited during daytime windows; validate practical info length in card expansion. Bring water and light rain jacket. | `Corcovado Mountain, Tijuca National Park, Rio de Janeiro - RJ` | 1 |  |
| `PARROT-RIO-FULL-TEST-2026` | 2 | `2026-09-19` | Day 2 - Corcovado, Boat & Wrap-up | Christ the Redeemer, controlled boat check-in and final feedback | `sun` | Validate in-trip progress, multiple scans, restrictions and feedback workflow. | Second operational simulation day. The group tests date-driven progress, controlled access, multiple QR scans and final feedback collection. | Restricted Boat Boarding | optional | `14:00` | 180 | Optional boat activity with two required scans per traveler. | Controlled activity. Scan 1 at boarding and scan 2 at return. Only boat add-on travelers should be allowed. Seasickness field should be reviewed before boarding. | `Marina da Gloria, Rio de Janeiro - RJ` | 2 | 250 |
| `PARROT-RIO-FULL-TEST-2026` | 2 | `2026-09-19` | Day 2 - Corcovado, Boat & Wrap-up | Christ the Redeemer, controlled boat check-in and final feedback | `sun` | Validate in-trip progress, multiple scans, restrictions and feedback workflow. | Second operational simulation day. The group tests date-driven progress, controlled access, multiple QR scans and final feedback collection. | Free time in Ipanema | suggested | `17:30` | 90 | Suggested free-time activity for recommendations and safety copy. | No formal check-in required; activity remains in app to validate suggested type. | `Ipanema, Rio de Janeiro - RJ` | 1 |  |
| `PARROT-RIO-FULL-TEST-2026` | 2 | `2026-09-19` | Day 2 - Corcovado, Boat & Wrap-up | Christ the Redeemer, controlled boat check-in and final feedback | `sun` | Validate in-trip progress, multiple scans, restrictions and feedback workflow. | Second operational simulation day. The group tests date-driven progress, controlled access, multiple QR scans and final feedback collection. | Final feedback circle | included | `19:30` | 60 | Closing session to collect live product feedback. | Staff sends final announcement before session. Ask each traveler to share one missing info and one useful feature. | `Copacabana, Rio de Janeiro - RJ` | 1 |  |

---

## 10. Atividades restritas - aba Participantes Atividades

### Regra

Quando uma atividade tiver linhas nesta aba, ela deve ser tratada como controlada. Apenas os telefones listados com `status = allowed` devem ser aceitos no check-in.

### Internal Parrot Ops Briefing

| trip_uuid | dia | atividade_nome | traveler_phone | status |
|---|---:|---|---|---|
| `PARROT-RIO-FULL-TEST-2026` | 1 | Internal Parrot Ops Briefing | `+15550001001` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Internal Parrot Ops Briefing | `+15550001002` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Internal Parrot Ops Briefing | `+15550001003` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Internal Parrot Ops Briefing | `+15550001004` | allowed |

### Sugarloaf Sunset Test

| trip_uuid | dia | atividade_nome | traveler_phone | status |
|---|---:|---|---|---|
| `PARROT-RIO-FULL-TEST-2026` | 1 | Sugarloaf Sunset Test | `+15550001001` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Sugarloaf Sunset Test | `+15550001002` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Sugarloaf Sunset Test | `+15550001003` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Sugarloaf Sunset Test | `+15550001004` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Sugarloaf Sunset Test | `+15550001005` | allowed |

### Restricted Boat Boarding

| trip_uuid | dia | atividade_nome | traveler_phone | status |
|---|---:|---|---|---|
| `PARROT-RIO-FULL-TEST-2026` | 2 | Restricted Boat Boarding | `+15550001001` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 2 | Restricted Boat Boarding | `+15550001002` | allowed |
| `PARROT-RIO-FULL-TEST-2026` | 2 | Restricted Boat Boarding | `+15550001008` | allowed |

### Casos negativos intencionais

Estes viajantes devem tentar escanear em atividades onde nao estao permitidos:

| traveler_phone | tentativa | resultado esperado |
|---|---|---|
| `+15550001005` | Internal Parrot Ops Briefing | rejeitado / nao permitido |
| `+15550001006` | Sugarloaf Sunset Test | rejeitado / nao permitido |
| `+15550001007` | Restricted Boat Boarding | rejeitado / nao permitido |

---

## 11. Tarefas de staff - aba Tarefas Staff

| trip_uuid | dia | atividade_nome | staff_phone | titulo | descricao | sort_order |
|---|---:|---|---|---|---|---:|
| `PARROT-RIO-FULL-TEST-2026` | 1 | Airport pickup - Santos Dumont | `+15550002002` | Confirm airport arrivals | Check Ana, Bruno and late-arrival scenario. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Hotel check-in and profile audit | `+15550002004` | Audit profile completeness | Ask each traveler to open profile, packages and service agreement. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Internal Parrot Ops Briefing | `+15550002003` | Run restricted QR test | Confirm allowed and denied scans. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Internal Parrot Ops Briefing | `+15550002005` | Scan two-step check-in | Scan each allowed traveler twice. | 2 |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Sugarloaf Sunset Test | `+15550002005` | Scan optional add-on travelers | Only allowed travelers should pass. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 1 | Anonymous notification drill | `+15550002002` | Send anonymous announcement | Validate traveler Notifications tab. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 2 | Corcovado early departure | `+15550002003` | Confirm Day 2 progress | Validate app switched to in-trip progress. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 2 | Christ the Redeemer Visit | `+15550002004` | Validate practical info | Ask travelers if details are clear. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 2 | Restricted Boat Boarding | `+15550002005` | Scan boarding and return | Scan 1 at boarding, scan 2 at return. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | 2 | Restricted Boat Boarding | `+15550002006` | Check seasickness risks | Review seasickness profile answers before boat. | 2 |
| `PARROT-RIO-FULL-TEST-2026` | 2 | Final feedback circle | `+15550002001` | Lead feedback session | Capture issues, missing info and wins. | 1 |

---

## 12. Contatos de staff - aba Contatos

| trip_uuid | category | name | role | phone | sort_order |
|---|---|---|---|---|---:|
| `PARROT-RIO-FULL-TEST-2026` | Parrot Ops | Marcelo Fazio | Product / Trip Lead | `+15550002001` | 1 |
| `PARROT-RIO-FULL-TEST-2026` | Parrot Ops | Ana Parrot | Traveler Support | `+15550002002` | 2 |
| `PARROT-RIO-FULL-TEST-2026` | Parrot Ops | Bruno Parrot | Operations Lead | `+15550002003` | 3 |
| `PARROT-RIO-FULL-TEST-2026` | Parrot Ops | Diego Parrot | QR Scanner | `+15550002005` | 4 |
| `PARROT-RIO-FULL-TEST-2026` | Emergency | SAMU | Ambulance emergency | `192` | 1 |
| `PARROT-RIO-FULL-TEST-2026` | Emergency | Military Police | Police emergency | `190` | 2 |
| `PARROT-RIO-FULL-TEST-2026` | Emergency | Fire Department | Fire emergency | `193` | 3 |
| `PARROT-RIO-FULL-TEST-2026` | Tourism | Riotur Tourist Info - Copacabana | Tourist information center | `+552125417522` | 1 |

---

## 13. Emergency Contacts - para InformationScreen

| trip_uuid | name | role | phone | sort_order |
|---|---|---|---|---:|
| `PARROT-RIO-FULL-TEST-2026` | Parrot Emergency Lead | Elisa Parrot | `+15550002006` | 1 |
| `PARROT-RIO-FULL-TEST-2026` | SAMU | Ambulance / medical emergency in Brazil | `192` | 2 |
| `PARROT-RIO-FULL-TEST-2026` | Military Police | Police emergency in Brazil | `190` | 3 |
| `PARROT-RIO-FULL-TEST-2026` | Fire Department | Fire and rescue in Brazil | `193` | 4 |
| `PARROT-RIO-FULL-TEST-2026` | Rio City Service | City service line | `1746` | 5 |

---

## 14. Recommendations - Local Tips

| trip_uuid | name | description | address | photo_url | sort_order |
|---|---|---|---|---|---:|
| `PARROT-RIO-FULL-TEST-2026` | Sugarloaf Mountain | Rio landmark reached by cable car from Praia Vermelha/Urca. Use this to validate image, map and tourist recommendation cards. | `Avenida Pasteur, 520 - Urca, Rio de Janeiro - RJ` | `https://example.com/recommendations/sugarloaf.jpg` | 1 |
| `PARROT-RIO-FULL-TEST-2026` | Christ the Redeemer | Major Rio landmark on Corcovado Mountain. Use as context for Day 2 itinerary and FAQ timing. | `Corcovado Mountain, Tijuca National Park, Rio de Janeiro - RJ` | `https://example.com/recommendations/christ.jpg` | 2 |
| `PARROT-RIO-FULL-TEST-2026` | Escadaria Selaron | Colorful mosaic staircase between Lapa and Santa Teresa, useful for a suggested photo stop. | `Rua Manuel Carneiro, Santa Teresa, Rio de Janeiro - RJ` | `https://example.com/recommendations/selaron.jpg` | 3 |
| `PARROT-RIO-FULL-TEST-2026` | Copacabana Tourist Information | Tourist information center listed by Riotur; useful for testing official-help recommendation. | `Av. Princesa Isabel, 183 - Copacabana, Rio de Janeiro - RJ` | `https://example.com/recommendations/copacabana-info.jpg` | 4 |
| `PARROT-RIO-FULL-TEST-2026` | Ipanema Free Time Area | Suggested free-time area for testing non-check-in activity and traveler safety copy. | `Ipanema, Rio de Janeiro - RJ` | `https://example.com/recommendations/ipanema.jpg` | 5 |

---

## 15. FAQ

| trip_uuid | question | answer | sort_order |
|---|---|---|---:|
| `PARROT-RIO-FULL-TEST-2026` | How do I log in? | Use your authorized WhatsApp number. The app sends an OTP code through WhatsApp. If the number is not authorized, login should be blocked. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | Where is my QR Code? | Open My Profile and expand My QR Code. Staff will scan it at controlled activities. | 2 |
| `PARROT-RIO-FULL-TEST-2026` | What happens if the camera scanner fails? | Staff should use the manual traveler list in the scanner panel and select your name. | 3 |
| `PARROT-RIO-FULL-TEST-2026` | Which activities are restricted? | Internal Parrot Ops Briefing, Sugarloaf Sunset Test and Restricted Boat Boarding have participant allowlists. | 4 |
| `PARROT-RIO-FULL-TEST-2026` | Why does the progress bar change automatically during the trip? | In in-trip mode, progress is based on each day start time instead of manual phase completion. | 5 |
| `PARROT-RIO-FULL-TEST-2026` | What emergency numbers should I know in Rio? | Medical emergency: 192. Police: 190. Fire department: 193. Rio city service: 1746. | 6 |
| `PARROT-RIO-FULL-TEST-2026` | What should I bring for outdoor activities? | Bring ID, water, sunscreen, comfortable shoes and a light rain jacket. Weather can change quickly around mountain viewpoints. | 7 |

---

## 16. Cancellation Policy / Regras do teste

Usar esta secao como regras operacionais da simulacao.

| trip_uuid | title | body | sort_order |
|---|---|---|---:|
| `PARROT-RIO-FULL-TEST-2026` | Data privacy | All traveler data in this dataset is fictitious. Replace phones only with explicit consent in real tests. | 1 |
| `PARROT-RIO-FULL-TEST-2026` | QR check-in rules | Staff must scan only through the staff view. For restricted activities, denied scans are expected and should be logged. | 2 |
| `PARROT-RIO-FULL-TEST-2026` | Progress reset | Re-importing trip content can reset checklist and phase progress. Avoid destructive imports after travelers start testing unless intentional. | 3 |
| `PARROT-RIO-FULL-TEST-2026` | Notification test | Send only pre-approved announcements during the simulation window. | 4 |
| `PARROT-RIO-FULL-TEST-2026` | Feedback | Each traveler should report one confusing step, one missing information item and one valuable feature. | 5 |

---

## 17. Announcements para teste

Estes comunicados devem ser criados pela Staff View durante a simulacao, nao necessariamente pre-carregados.

| momento | staff_phone | title | body | is_anonymous | validacao |
|---|---|---|---|---|---|
| Dia 1 12:15 | `+15550002002` | Welcome to the Rio simulation | Please open the app, confirm your profile and keep your QR Code ready for the briefing. | false | Deve aparecer na tela Notifications com remetente. |
| Dia 1 20:00 | `+15550002002` | Tomorrow departure update | Departure moved to 08:15. Meet in the lobby with ID, water and sunscreen. | true | Deve aparecer sem nome do remetente. |
| Dia 2 13:30 | `+15550002005` | Boat QR check-in | Boat boarding requires two scans: one at boarding and one at return. | false | Deve aparecer antes da atividade restrita. |
| Dia 2 19:00 | `+15550002001` | Final feedback session | Please join the final feedback circle and share one friction, one missing info item and one feature that helped. | false | Deve abrir como notificacao mais recente. |

---

## 18. Lista de QR Codes a criar

O app gera QR payload assinado por backend usando `trip_traveler_id` e `trip_uuid`. Portanto, os valores abaixo sao identificadores de teste para organizar a criacao. Depois que os usuarios forem inseridos no banco, gerar o QR real via `GET /me/qr-code` ou pela funcao `create_traveler_qr_payload`.

### QR Codes validos de viajantes

| qr_label | traveler_phone | expected_name | trip_uuid | deve_funcionar_em |
|---|---|---|---|---|
| `QR-ANA-VALID` | `+15550001001` | Ana Martins | `PARROT-RIO-FULL-TEST-2026` | todas as atividades gerais, Ops Briefing, Sugarloaf, Boat |
| `QR-BRUNO-VALID` | `+15550001002` | Bruno Lee | `PARROT-RIO-FULL-TEST-2026` | todas as atividades gerais, Ops Briefing, Sugarloaf, Boat |
| `QR-CAMILA-VALID` | `+15550001003` | Camila Rocha | `PARROT-RIO-FULL-TEST-2026` | todas as atividades gerais, Ops Briefing, Sugarloaf |
| `QR-DANIEL-VALID` | `+15550001004` | Daniel Kim | `PARROT-RIO-FULL-TEST-2026` | todas as atividades gerais, Ops Briefing, Sugarloaf |
| `QR-ELENA-VALID` | `+15550001005` | Elena Costa | `PARROT-RIO-FULL-TEST-2026` | atividades gerais, Sugarloaf |
| `QR-FELIPE-VALID` | `+15550001006` | Felipe Santos | `PARROT-RIO-FULL-TEST-2026` | atividades gerais somente |
| `QR-GABI-VALID` | `+15550001007` | Gabriela Torres | `PARROT-RIO-FULL-TEST-2026` | atividades gerais somente |
| `QR-HUGO-VALID` | `+15550001008` | Hugo Almeida | `PARROT-RIO-FULL-TEST-2026` | atividades gerais, Boat |

### QR Codes invalidos/provocacoes

| qr_label | payload_tipo | resultado esperado |
|---|---|---|
| `QR-INVALID-WRONG-TRIP` | QR real de outro `trip_uuid` | rejeitar por viagem incorreta |
| `QR-INVALID-BAD-SIGNATURE` | token editado manualmente | rejeitar por assinatura invalida |
| `QR-INVALID-UNKNOWN-TRAVELER` | token com `trip_traveler_id` inexistente | rejeitar por viajante nao encontrado |
| `QR-INVALID-STAFF-AS-TRAVELER` | token de usuario staff sem traveler valido | rejeitar |
| `QR-DUPLICATE-ANA-BRIEFING-STEP-3` | terceiro scan em atividade com max_checkins = 2 | retornar already_checked_in |
| `QR-DENIED-ELENA-BRIEFING` | Elena tentando Ops Briefing | rejeitar por nao estar em allowlist |
| `QR-DENIED-FELIPE-SUGARLOAF` | Felipe tentando Sugarloaf | rejeitar por nao estar em allowlist |
| `QR-DENIED-GABI-BOAT` | Gabi tentando Boat | rejeitar por nao estar em allowlist |

### Matriz de scan esperada

| atividade | max_scans | participante | scan 1 | scan 2 | scan 3 |
|---|---:|---|---|---|---|
| Internal Parrot Ops Briefing | 2 | Ana | checked_in | checked_in | already_checked_in |
| Internal Parrot Ops Briefing | 2 | Bruno | checked_in | checked_in | already_checked_in |
| Internal Parrot Ops Briefing | 2 | Elena | denied | denied | denied |
| Sugarloaf Sunset Test | 1 | Camila | checked_in | already_checked_in | already_checked_in |
| Sugarloaf Sunset Test | 1 | Felipe | denied | denied | denied |
| Restricted Boat Boarding | 2 | Hugo | checked_in | checked_in | already_checked_in |
| Restricted Boat Boarding | 2 | Gabi | denied | denied | denied |

---

## 19. Dados de importacao em formato de planilha

### Viagens

```text
trip_uuid,nome_da_viagem,data_inicio,data_fim,service_agreement_url
PARROT-RIO-FULL-TEST-2026,Parrot Rio Full App Simulation,2026-09-18,2026-09-19,https://parrottrips.com/test/service-agreement-parrot-rio-full-app-simulation.pdf
```

### Staff

```text
trip_uuid,phone,nome,funcao,photo_url,bio
PARROT-RIO-FULL-TEST-2026,+15550002001,Marcelo Fazio,Product / Trip Lead,https://example.com/staff/marcelo.jpg,Lidera a simulacao valida UX e operacao
PARROT-RIO-FULL-TEST-2026,+15550002002,Ana Parrot,Traveler Support,https://example.com/staff/ana-parrot.jpg,Responsavel por suporte aos viajantes e comunicados
PARROT-RIO-FULL-TEST-2026,+15550002003,Bruno Parrot,Operations Lead,https://example.com/staff/bruno-parrot.jpg,Coordena check-ins horarios e fornecedores
PARROT-RIO-FULL-TEST-2026,+15550002004,Clara Parrot,Content Manager,https://example.com/staff/clara-parrot.jpg,Valida roteiro FAQ recomendacoes e textos no app
PARROT-RIO-FULL-TEST-2026,+15550002005,Diego Parrot,QR Scanner,https://example.com/staff/diego-parrot.jpg,Opera scanner QR e contingencia manual
PARROT-RIO-FULL-TEST-2026,+15550002006,Elisa Parrot,Emergency Contact,https://example.com/staff/elisa-parrot.jpg,Ponto focal de saude seguranca e emergencias
```

---

## 20. Plano de validacao

### Pre-trip

- Login OTP com todos os viajantes.
- Login OTP com todos os staff.
- Verificar Home em modo `pre-trip`.
- Marcar checklists em cada fase.
- Marcar fase como completa.
- Confirmar que o usuario anda no jogo da vida.
- Confirmar que o ideal pace aparece na fase `Operational Checklist`.
- Abrir perfil e salvar todos os campos.
- Abrir Service Agreement.
- Verificar Packages e add-ons.
- Abrir QR Code de cada viajante.

### In-trip

- Trocar `trip_settings.mode` para `in-trip`.
- Confirmar que a barra usa somente dias in-trip.
- Confirmar que Day 1 aparece como iniciado quando `starts_at <= now`.
- Abrir DayDetails para Dia 1 e Dia 2.
- Expandir atividades com practical_info.
- Validar labels included/optional/suggested/logistics.
- Enviar notificacoes.
- Abrir InformationScreen.
- Validar equipe, contatos, emergency contacts, local tips, FAQ e regras.

### Staff

- Entrar como cada staff.
- Abrir Staff View.
- Validar itinerary por dia.
- Ver tarefas por atividade.
- Abrir scanner.
- Escanear QR valido.
- Escanear QR duplicado.
- Escanear QR de viajante nao permitido.
- Usar fallback manual por lista de nomes.
- Conferir absent travelers.
- Conferir contagem por step em atividade com `max_checkins = 2`.
- Enviar, editar e apagar anuncio proprio.

---

## 21. Referencias publicas usadas

- Rio de Janeiro official tourist information / Riotur: https://riotur.rio/en/secao/tourist-information/
- Sugarloaf information on Riotur, including address at Avenida Pasteur, 520: https://riotur.rio/en/que_fazer/sugarloaf/
- Rio useful emergency numbers, including 192, 193, 190 and 1746: https://www.riocomsaude.rj.gov.br/hotsite/english/telefonesuteis.php
- SAMU 192, Ministerio da Saude: https://www.gov.br/saude/pt-br/composicao/saes/samu-192
- Brazil travel information, U.S. State Department: https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Brazil.html
- Christ the Redeemer visiting-hours reference used only as planning context: https://www.cristoredentor.net.br/en/visiting-hours
- Escadaria Selaron public context: https://escadariaselaron.rio.br/

---

## 22. Observacoes finais

- Este arquivo e propositalmente completo para validar o app inteiro.
- Antes de rodar em ambiente real, trocar telefones ficticios por telefones autorizados.
- QR Codes reais devem ser gerados depois que `users` e `trip_travelers` existirem no banco.
- Atividades restritas devem ter linhas em `Participantes Atividades`; caso contrario, o staff view considera todos os viajantes esperados.
- Em atividades com `max_checkins = 2`, validar scan 1 e scan 2 separadamente.
- Reimportar conteudo de viagem pode apagar progresso e dados operacionais ligados a fases/atividades. Fazer isso antes da validacao com usuarios reais.

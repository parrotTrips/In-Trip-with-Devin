# RFID / NFC — Controle de Presença de Viajantes

Pesquisa sobre tecnologias de identificação à distância para o contexto da Parrot Trips.

---

## O que você imaginou e como se chama tecnicamente

A ideia de "apontar um leitor para pulseiras nos braços dos viajantes e contar/identificar à distância" corresponde exatamente ao **UHF RFID passivo** — a mesma tecnologia que a Disney usou no MagicBand desde 2013 para rastrear visitantes pelo parque sem que eles precisassem fazer nada.

---

## Como o Disney MagicBand funciona (referência de mercado)

O MagicBand tem **3 rádios diferentes**:

| Rádio | Frequência | Alcance | Uso |
|---|---|---|---|
| NFC passivo | 13.56 MHz | ~4 cm (toque) | Entrada do parque, pagamento, chave do quarto |
| UHF passivo | 915 MHz | ~6 metros | Rastreamento de localização no parque |
| Ativo proprietário | 2.4 GHz (Nordic nRF24LE1) | ~30 metros | Experiências personalizadas, fotos nas atrações |

O rádio UHF de 915 MHz é o que permite identificar visitantes à distância sem ação deles — exatamente o que você descreveu.

**Custo do sistema:** Disney investiu ~US$ 1 bilhão na infraestrutura completa (parque inteiro com milhares de leitores fixos, backend, integração). Em 2026, a Disney está **desativando os MagicBands** e migrando as mesmas funções para o app no celular via NFC — o smartphone virou o substituto.

---

## As três tecnologias relevantes para o contexto da Parrot

### 1. UHF RFID (915 MHz) — "leitura à distância"

**Como funciona:** Leitor emite campo eletromagnético. Pulseira passiva (sem bateria) responde com seu ID. Alcance: 1–9 metros dependendo da antena.

**Hardware necessário:**
- Pulseiras/tags UHF descartáveis: **US$ 0,10–0,50 por unidade**
- Leitor fixo (ex: Zebra FX9600): **US$ 800–1.500**
- Leitor handheld (ex: Zebra RFD8500): **US$ 2.000–3.500**
- SDK Android: gratuito (Zebra RFID SDK)

**Para grupos de 10–20 pessoas:** Viável tecnicamente, mas o custo do leitor (US$ 2.000+) é desproporcional ao tamanho do grupo. Faz sentido para parques com 10.000+ visitantes/dia, não para viagens de 15 pessoas.

**Integração com o app:** Requer hardware externo (leitor Zebra via Bluetooth) — não é o NFC nativo do celular.

---

### 2. NFC (13.56 MHz) — "toque com o celular"

**Como funciona:** O staff abre o app, aponta o celular para a pulseira/tag do viajante a ~4 cm e registra a presença. É o NFC nativo de qualquer iPhone (7+) ou Android.

**Hardware necessário:**
- Tags NFC passivas (NTAG213/215/216): **US$ 0,05–0,30 por unidade** — podem ser impressas em pulseiras de evento
- Leitor: **o próprio celular do staff** — sem custo adicional

**Para grupos de 10–20 pessoas:** Custo quase zero em hardware. O staff já tem o celular. Uma pulseira NFC por viajante (~R$ 1–2 cada).

**Integração com o app:** `react-native-nfc-manager` (React Native) ou CoreNFC (iOS nativo) — bibliotecas maduras, bem mantidas, sem hardware adicional.

---

### 3. QR Code — "câmera do celular"

**Como funciona:** Viajante mostra o QR Code na tela do app. Staff escaneia com a câmera. Ou vice-versa.

**Hardware necessário:** Zero — câmera do celular.

**Para grupos de 10–20 pessoas:** A solução mais simples e a que foi decidida para o Parrot Trips (Modelo A).

---

## Empresas de pulseiras RFID para eventos (referência de mercado)

### Internacional
| Empresa | Foco | Contato |
|---|---|---|
| [Intellitix](https://intellitix.com) | Festivais (Coachella, Rock in Rio) | intellitix.com |
| [ID&C](https://www.idcband.com) | Fabricante de pulseiras RFID | idcband.com |
| [Glownet](https://glownet.com) | Eventos cashless + controle | glownet.com |
| [WRSTBND](https://www.wrstbnd.com) | Ticketing + RFID | wrstbnd.com |

### Brasil
| Empresa | Foco | Contato |
|---|---|---|
| [PasseVIP](https://passevip.com.br) | Rock in Rio, The Town, Lollapalooza | passevip.com.br |
| [Zig](https://blog.zig.fun) | Cashless + ticketing integrado | zig.fun |
| [Controlbar](https://www.sistemacontrolbar.com.br) | Bares em eventos | +55 81 97338-2288 |
| [Cashless Fácil](https://cashlessfacil.com.br) | Eventos menores | cashlessfacil.com.br |

**Nota:** Nenhuma empresa publica pricing. Todos trabalham por orçamento. O modelo típico é: taxa por participante + percentual sobre transações + aluguel de hardware.

---

## Recomendação para a Parrot Trips

### Curto prazo (implementar agora): QR Code

Já decidido — staff escaneia o QR do viajante. Custo zero, sem hardware adicional, funciona hoje.

**O que falta implementar no app:**
- Tela no app do **viajante** com o QR Code fixo (baseado no `user_id`)
- Câmera no app do **staff** para escanear e registrar presença na atividade

### Médio prazo (se houver demanda): NFC

Se o QR Code gerar atrito operacional (viajante não abre o app rápido o suficiente, tela bloqueada, etc.), migrar para **pulseiras NFC** é a evolução natural:

- Pulseiras impressas com tag NFC (NTAG213) por ~R$ 1–2 cada
- Staff usa o mesmo celular com o app já existente
- Leitura em ~1 segundo, sem depender do viajante abrir o app
- Implementação: `react-native-nfc-manager` no frontend (sem hardware adicional)

### Não recomendado agora: UHF RFID

Hardware caro (US$ 2.000+), infraestrutura complexa, desproporcional para grupos de 10–20 pessoas. Faz sentido apenas se a Parrot escalar para operações com centenas de participantes simultâneos.

---

## Contexto histórico relevante

A Disney está **desativando os MagicBands físicos** em 2025–2026 e migrando para o app no celular (MagicMobile) usando NFC. A tendência da indústria confirma: o smartphone com NFC é o substituto natural das pulseiras para identificação individual. O UHF de longa distância continua relevante para rastreamento passivo em larga escala — não para check-in individual em grupos pequenos.

---

## Fontes

- [Disney MagicBand Teardown — Adafruit](https://learn.adafruit.com/magic-band-teardown)
- [Dissecting Disney's MagicBand — EE Times](https://www.eetimes.com/dissecting-disneys-magicband/)
- [9 Ways Disney Uses RFID — Atlas RFID Store](https://www.atlasrfidstore.com/rfid-insider/9-ways-disney-uses-rfid-nfc-technology-disneys-continued-rfid-success/)
- [Disney phasing out MagicBand — Inside the Magic (2026)](https://insidethemagic.net/2026/06/disney-appears-to-be-phasing-out-magicbands-at-disney-world-and-disneyland-rl1/)
- [react-native-nfc-manager — GitHub](https://github.com/revtel/react-native-nfc-manager)
- [iOS CoreNFC — Apple Developer](https://developer.apple.com/documentation/corenfc)
- [Android NFC Basics — Google](https://developer.android.com/develop/connectivity/nfc/nfc)
- [Smart Theme Park Wristband Market 2033 — MarketIntelo](https://marketintelo.com/report/smart-theme-park-wristband-market/amp)

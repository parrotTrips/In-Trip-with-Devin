# Staff Activity Tasks Design

## Contexto

O app do staff hoje mostra os dias da viagem e as atividades do roteiro, mas não mostra as tarefas operacionais de cada membro da equipe. A operação precisa cadastrar essas tarefas pela planilha de staff e fazer com que cada staff veja apenas as tarefas atribuídas a ele dentro de cada atividade do dia.

Esta entrega vem antes do QR Code porque organiza a rotina operacional do staff no app. Depois, o fluxo de QR Code pode usar a mesma estrutura de atividade para registrar presença.

## Decisões aprovadas

- Cada tarefa de staff pertence a uma atividade específica do roteiro.
- Cada tarefa é atribuída a um membro específico da staff.
- O app mostra o roteiro completo, mas cada staff vê apenas as tarefas atribuídas ao próprio usuário.
- A planilha usa `atividade_nome` como referência humana, não ID técnico.
- A tarefa não tem horário próprio. Ela herda o contexto da atividade do roteiro.
- A ordem entre tarefas é controlada por `sort_order`.

## Aba nova na planilha de staff

Adicionar a aba `Tarefas Staff` na planilha `Parrot Trips — Staff`.

Colunas:

| Coluna | Descrição |
| --- | --- |
| `trip_uuid` | Identificador da viagem. |
| `dia` | Número do dia no roteiro, igual ao campo `dia` da aba `Roteiro`. |
| `atividade_nome` | Nome da atividade do roteiro. |
| `staff_phone` | Telefone do staff responsável pela tarefa. |
| `titulo` | Título curto da tarefa. |
| `descricao` | Descrição operacional da tarefa. |
| `sort_order` | Ordem da tarefa dentro da atividade para aquele staff. |

Exemplo:

```text
trip_uuid | dia | atividade_nome | staff_phone | titulo | descricao | sort_order
TEST-2026-FULL | 1 | Airport Transfer | +5511999990001 | Coordenar van 1 | Receber viajantes no aeroporto e direcionar para a van correta | 1
TEST-2026-FULL | 1 | Airport Transfer | +5511999990002 | Confirmar fornecedor | Falar com motorista e confirmar saída | 1
```

## Banco de dados

A tabela `staff_tasks` já existe, mas hoje não está ligada diretamente a `trip_activities`. A entrega deve evoluir essa tabela adicionando `trip_activity_id`.

Campos relevantes:

- `trip_phase_id`: mantém o vínculo com o dia/fase.
- `trip_activity_id`: novo vínculo com a atividade do roteiro.
- `assigned_to_user_id`: staff responsável.
- `title`: título curto da tarefa.
- `description`: descrição operacional.
- `sort_order`: ordem de exibição.

## Importação

O import da planilha de staff deve ler a aba `Tarefas Staff`.

Para cada linha:

1. Encontrar o usuário staff por `staff_phone`.
2. Encontrar o dia por `trip_uuid + dia`.
3. Encontrar a atividade por `atividade_nome` dentro daquele dia.
4. Salvar a tarefa em `staff_tasks`.

O import deve falhar com mensagem clara quando:

- o staff não existir;
- o dia não existir;
- a atividade não existir;
- houver mais de uma atividade com o mesmo nome no mesmo dia.

## API

O endpoint `GET /me/staff/trip` deve continuar retornando dias e atividades do roteiro. Para cada atividade, deve incluir apenas as tarefas atribuídas ao staff logado.

Formato esperado dentro de cada atividade:

```json
{
  "id": "activity-id",
  "name": "Airport Transfer",
  "staff_tasks": [
    {
      "id": "task-id",
      "title": "Coordenar van 1",
      "description": "Receber viajantes no aeroporto e direcionar para a van correta",
      "sort_order": 1
    }
  ]
}
```

## App do staff

Na aba `Itinerary`, ao abrir uma atividade, o app deve mostrar uma seção `My tasks` com as tarefas daquele staff para aquela atividade.

Se o staff não tiver tarefa naquela atividade, a tela pode não mostrar a seção para evitar ruído visual.

## Validação

Validar com a viagem `TEST-2026-FULL`:

- cadastrar tarefas de exemplo para pelo menos dois staffs;
- importar a aba `Tarefas Staff`;
- abrir o app como cada staff;
- confirmar que cada staff vê apenas as próprias tarefas dentro da atividade correta.

## Relação com QR Code

Depois desta entrega, a implementação do QR Code deve registrar presença por atividade e salvar o staff que fez o scan em `checked_in_by`.

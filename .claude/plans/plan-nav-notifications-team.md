# Plano — Nav, Notifications, Parrot Team

## Resumo das mudanças

### Frontend — viajante
1. Remover Amount Paid do ProfileScreen
2. QR Code move para dentro do ProfileScreen como CollapsibleSection
3. Renomear "Map" → "Journey" no BottomNav
4. Nav final: Journey | Notifications | My Profile | Parrot Team
5. Nova tela NotificationsScreen (leitura de anúncios)
6. Nova tela ParrotTeamScreen (cards do staff com WhatsApp)
7. Remover rota /qr-code e arquivo QrCodeScreen

### Frontend — staff
8. Nova aba "Announce" no StaffScreen com formulário de envio (título + mensagem)

### Backend
9. Novo endpoint GET /me/announcements — retorna anúncios da viagem do viajante
10. Novo endpoint POST /me/staff/announcements — staff envia anúncio (valida role=staff)
11. Novo endpoint GET /me/team — retorna membros do staff da viagem (nome, função, telefone, photo_url, bio)

### Banco de dados (2 migrations)
12. Migration 0012: tabela trip_announcements (id, trip_uuid, title, body, sent_by_user_id, created_at)
13. Migration 0013: ALTER TABLE trip_staff ADD COLUMN photo_url TEXT, ADD COLUMN bio TEXT

### Planilha Staff
14. CodeStaff.gs: adicionar colunas photo_url e bio na aba Staff (no setupSheetHeaders)

## Ordem de implementação
1. Migrations (banco primeiro)
2. Modelos SQLAlchemy
3. Endpoints backend
4. Frontend: remover Amount Paid, mover QR Code para Profile, renomear Map→Journey
5. Frontend: NotificationsScreen + ParrotTeamScreen
6. Frontend: BottomNav com 4 itens
7. Frontend: aba Announce no StaffScreen
8. Router: adicionar /notifications e /team, remover /qr-code
9. Planilha: atualizar CodeStaff.gs
10. Deploy backend → deploy frontend

# Plano — Information tab, Notifications bell, Packages rename

## 1. Products & Payment → Packages
- ProfileScreen.tsx: trocar título e emoji da CollapsibleSection

## 2. Notifications sai do footer → sininho no TopBar
- BottomNav.tsx: remover item Notifications, Parrot Team → Information, nav fica com 3 itens: Journey | My Profile | Information
- TopBar.tsx: adicionar prop `showNotifications` e botão Bell no canto direito que navega para /notifications
- HomeScreen.tsx: passar showNotifications=true no TopBar (ou tornar padrão)

## 3. /team → /information com 3 sub-seções
- Renomear rota /team → /information no router.tsx
- Criar InformationScreen.tsx substituindo ParrotTeamScreen com 3 abas internas:
  - Parrot Team (conteúdo atual do ParrotTeamScreen)
  - Emergency Contacts
  - Local Recommendations

## 4. Emergency Contacts
- Migration 0017: tabela trip_emergency_contacts (id, wetravel_trip_uuid, name, role, phone, sort_order)
- Modelo SQLAlchemy
- Endpoint GET /me/emergency-contacts
- Aba na planilha de conteúdo (Code.gs): "Emergency Contacts" com colunas trip_uuid, name, role, phone, sort_order
- Import no admin_service.py
- Frontend: lista de cards com nome, role e botão WhatsApp

## 5. Local Recommendations
- Migration 0017 (mesma): tabela trip_recommendations (id, wetravel_trip_uuid, name, description, address, photo_url, sort_order)
- Modelo SQLAlchemy
- Endpoint GET /me/recommendations
- Aba na planilha de conteúdo (Code.gs): "Recomendacoes" com colunas trip_uuid, name, description, address, photo_url, sort_order
- Import no admin_service.py
- Frontend: cards com foto, nome, descrição e endereço linkado ao Google Maps

## Ordem de implementação
1. Migration + modelos
2. Endpoints backend
3. Import planilha (admin_service + Code.gs)
4. Frontend: ProfileScreen (rename), TopBar (bell), BottomNav (3 itens), InformationScreen, router
5. Deploy backend → deploy frontend

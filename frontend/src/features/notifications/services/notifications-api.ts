import { request } from '../../../shared/api/client';

export interface Notification {
  id: number;
  title: string;
  body: string;
  type: string;
  link: string | null;
  read: boolean;
  created_at: string;
}

export interface NotificationsResponse {
  notifications: Notification[];
  unread_count: number;
}

export async function getNotifications(userId: number, unreadOnly = false) {
  const params = unreadOnly ? '?unread_only=true' : '';
  return request<NotificationsResponse>(`/notifications/${userId}${params}`);
}

export async function getUnreadCount(userId: number) {
  return request<{ unread_count: number }>(`/notifications/${userId}/count`);
}

export async function markNotificationRead(notificationId: number) {
  return request<{ message: string }>(`/notifications/${notificationId}/read`, {
    method: 'PUT',
  });
}

export async function markAllNotificationsRead(userId: number) {
  return request<{ message: string }>(`/notifications/${userId}/read-all`, {
    method: 'PUT',
  });
}

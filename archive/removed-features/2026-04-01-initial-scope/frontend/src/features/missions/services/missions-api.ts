import { request } from '../../../shared/api/client';

export interface Mission {
  id: number;
  title: string;
  description: string;
  points: number;
  icon: string;
  category: string;
  completed: boolean;
}

export interface MissionsResponse {
  trip_id: string;
  missions: Mission[];
}

export interface LeaderboardEntry {
  user_id: number;
  name: string;
  total_points: number;
  missions_completed: number;
}

export interface LeaderboardResponse {
  trip_id: string;
  leaderboard: LeaderboardEntry[];
}

export async function getMissions(tripId: string, userId?: number) {
  const params = userId ? `?user_id=${userId}` : '';
  return request<MissionsResponse>(`/missions/${tripId}${params}`);
}

export async function completeMission(tripId: string, userId: number, missionId: number) {
  return request<{ message: string; points_earned: number; already_completed: boolean }>(
    `/missions/${tripId}/complete?user_id=${userId}`,
    { method: 'POST', body: JSON.stringify({ mission_id: missionId }) }
  );
}

export async function uncompleteMission(tripId: string, userId: number, missionId: number) {
  return request<{ message: string }>(
    `/missions/${tripId}/uncomplete?user_id=${userId}`,
    { method: 'DELETE', body: JSON.stringify({ mission_id: missionId }) }
  );
}

export async function getLeaderboard(tripId: string) {
  return request<LeaderboardResponse>(`/missions/${tripId}/leaderboard`);
}

export async function getUserPoints(tripId: string, userId: number) {
  return request<{ user_id: number; total_points: number; missions_completed: number }>(
    `/missions/${tripId}/user/${userId}/points`
  );
}

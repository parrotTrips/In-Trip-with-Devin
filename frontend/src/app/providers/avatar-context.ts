import { createContext, useContext } from 'react';

const storageKey = (userId: string) => `parrot_avatar_${userId}`;

export function loadStoredAvatar(userId: string): string | null {
  try {
    return localStorage.getItem(storageKey(userId));
  } catch {
    return null;
  }
}

export function persistAvatar(userId: string, url: string | null) {
  try {
    if (url) {
      localStorage.setItem(storageKey(userId), url);
    } else {
      localStorage.removeItem(storageKey(userId));
    }
  } catch {
    // ignore
  }
}

export function clearStoredAvatar(userId: string) {
  try {
    localStorage.removeItem(storageKey(userId));
  } catch {
    // ignore
  }
}

interface AvatarContextType {
  avatarUrl: string | null;
  setAvatarUrl: (url: string | null) => void;
}

export const AvatarContext = createContext<AvatarContextType>({
  avatarUrl: null,
  setAvatarUrl: () => {},
});

export function useAvatar() {
  return useContext(AvatarContext);
}

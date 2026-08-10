import { createContext, useContext } from 'react';

interface StaffViewContextType {
  onSwitchToStaffView: (() => void) | null;
}

export const StaffViewContext = createContext<StaffViewContextType>({
  onSwitchToStaffView: null,
});

export function useStaffView() {
  return useContext(StaffViewContext);
}

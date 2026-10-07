import { LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';

import { useAuth } from '../auth/auth-context';
import { Button } from '@/components/ui/button';

/** Barra superior comum a todas as telas logadas. */
export default function ConsoleHeader() {
  const { principal, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/95 px-4 backdrop-blur">
      <Link to="/" className="flex items-center gap-2">
        <img src="/parrot_icon.svg" alt="" className="h-7 w-7" />
        <span className="font-semibold tracking-tight">Parrot Trips</span>
        <span className="hidden text-sm text-muted-foreground sm:inline">· Console de conteúdo</span>
      </Link>
      {principal && (
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground sm:inline">{principal.email}</span>
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Sair
          </Button>
        </div>
      )}
    </header>
  );
}

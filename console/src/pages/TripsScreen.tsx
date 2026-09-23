import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { listTrips, PRE_DEPARTURE_LINK, type Trip } from '../api/console-api';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function TripsScreen() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    listTrips()
      .then(data => setTrips(data.trips))
      .catch(err => setError((err as Error).message));
  }, []);

  const copyLink = async () => {
    await navigator.clipboard.writeText(PRE_DEPARTURE_LINK);
    setCopied(true);
  };

  return (
    <div className="mx-auto max-w-3xl p-8">
      <div className="mb-6 flex items-center gap-3">
        <img src="/parrot_icon.svg" alt="" className="h-8 w-8" />
        <h1 className="text-2xl font-bold tracking-tight">Viagens</h1>
      </div>

      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

      <ul className="mb-6 space-y-2">
        {trips.map(trip => (
          <li key={trip.trip_uuid}>
            <Card className="transition-colors hover:border-primary/40">
              <CardContent>
                <Link
                  to={`/trips/${trip.trip_uuid}/fases`}
                  className="font-medium text-foreground hover:text-primary"
                >
                  {trip.title}
                </Link>
                <p className="text-sm text-muted-foreground">
                  {trip.start_date} — {trip.end_date}
                </p>
              </CardContent>
            </Card>
          </li>
        ))}
      </ul>

      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={copyLink}>Copiar link de pré-embarque</Button>
        {copied && <span className="text-sm text-primary">Copiado</span>}
      </div>
    </div>
  );
}

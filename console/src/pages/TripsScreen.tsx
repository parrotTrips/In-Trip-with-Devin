import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { listTrips, PRE_DEPARTURE_LINK, type Trip } from '../api/console-api';

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
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-xl font-bold mb-4">Viagens</h1>
      <p className="border border-amber-300 bg-amber-50 text-amber-900 rounded p-3 text-sm mb-4">
        Não importe esta viagem pela planilha depois de editá-la aqui. O import legado pode
        substituir fases, checklist e links.
      </p>
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
      <ul className="space-y-2 mb-6">
        {trips.map(trip => (
          <li key={trip.trip_uuid} className="border rounded p-3">
            <Link to={`/trips/${trip.trip_uuid}/phases`} className="font-medium underline">
              {trip.title}
            </Link>
            <p className="text-sm text-gray-600">
              {trip.start_date} — {trip.end_date}
            </p>
          </li>
        ))}
      </ul>
      <button onClick={copyLink} className="border rounded px-3 py-2">
        Copiar link de pré-embarque
      </button>
      {copied && <span className="ml-2 text-sm text-green-700">Copiado</span>}
    </div>
  );
}

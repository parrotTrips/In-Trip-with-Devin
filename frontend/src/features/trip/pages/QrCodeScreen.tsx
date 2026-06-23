import { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';

import { useAuth } from '../../../app/providers/auth-context';
import { useTripContext } from '../../../app/providers/trip-context';
import { getMyQrCode, type TravelerQrCode } from '../services/trip-api';
import TopBar from '../../../shared/components/TopBar';

export default function QrCodeScreen() {
  const { user } = useAuth();
  const { tripInfo, loading, error } = useTripContext();
  const [qrCode, setQrCode] = useState<TravelerQrCode | null>(null);

  const travelerName = user?.name ?? user?.phone ?? 'Traveler';
  const displayTitle = tripInfo?.title ?? 'Sua Viagem';

  useEffect(() => {
    let active = true;

    getMyQrCode()
      .then((result) => {
        if (active) setQrCode(result);
      })
      .catch(() => {
        if (active) setQrCode(null);
      });

    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-emerald-50 pb-20">
        <TopBar title="Carregando..." />
        <div className="pt-14 flex flex-col items-center justify-center h-64 gap-3">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-sm">Carregando sua viagem...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-emerald-50 pb-20">
        <TopBar title="Parrot Trips" />
        <div className="pt-14 flex flex-col items-center justify-center h-64 gap-4 px-6">
          <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center text-2xl">⚠️</div>
          <p className="text-gray-700 font-semibold text-center">Não conseguimos carregar sua viagem</p>
          <p className="text-gray-400 text-sm text-center">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-emerald-50 pb-20">
      <TopBar title={displayTitle} />

      <div className="pt-14 px-4">
        <section className="max-w-lg mx-auto rounded-2xl border border-emerald-100 bg-white shadow-sm p-4">
          <div className="flex items-center gap-4">
            <div className="shrink-0 rounded-xl border border-gray-100 bg-white p-2">
              {qrCode && (
                <QRCodeSVG
                  value={qrCode.qr_payload}
                  size={160}
                  level="M"
                  aria-label="Traveler check-in QR code"
                />
              )}
            </div>
            <div className="min-w-0">
              <h2 className="text-base font-semibold text-gray-800 font-[Fredoka]">
                My QR Code
              </h2>
              <p className="mt-1 truncate text-sm font-medium text-gray-700">{travelerName}</p>
              <p className="truncate text-sm text-emerald-700">{displayTitle}</p>
              <p className="mt-2 text-xs leading-5 text-gray-500">
                Present this QR code to staff for check-in.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

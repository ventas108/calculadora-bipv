import { AlertCircle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-[#f4f0e6] px-6">
      <section className="w-full max-w-md rounded-2xl border border-[#d9d2c2] bg-[#fbf8f0] p-8 shadow-[0_12px_30px_rgba(24,48,56,.08)]">
        <div className="flex gap-3">
          <AlertCircle className="h-8 w-8 text-[#a56b0b]" aria-hidden="true" />
          <h1 className="text-2xl font-bold text-[#19363a]">Página no encontrada</h1>
        </div>
        <p className="mt-4 text-sm leading-6 text-[#71807c]">
          La ruta solicitada no pertenece al espacio de trabajo BIPV Colombia.
        </p>
      </section>
    </div>
  );
}

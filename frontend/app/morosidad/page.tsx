"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

const PREGUNTA_MOROSIDAD = "(Pregunta 100% ANÓNIMA): En los últimos 12 meses, ¿te has retrasado más de 30 días en el pago de alguna obligación (tarjeta, préstamo, cuota de estudios, o recibo de servicios)?";

const OPCIONES_MOROSIDAD = [
  {
    value: "Sí, me he retrasado o he tenido dificultades para pagar en la fecha indicada.",
    label: "Sí, me he retrasado o he tenido dificultades para pagar en la fecha indicada.",
  },
  {
    value: "No, siempre he pagado todas mis obligaciones a tiempo",
    label: "No, siempre he pagado todas mis obligaciones a tiempo.",
  },
  {
    value: "No he tenido ninguna obligación o deuda a mi nombre en el último año.",
    label: "No he tenido ninguna obligación o deuda a mi nombre en el último año.",
  },
];

export default function Morosidad() {
  const router = useRouter();
  const [respuesta, setRespuesta] = useState<string>("");
  const [error, setError] = useState("");

  useEffect(() => {
    const saved = sessionStorage.getItem("respuesta_morosidad");
    if (saved) setRespuesta(saved);
  }, []);

  const handleContinuar = () => {
    if (!respuesta) {
      setError("Por favor selecciona una opción para continuar.");
      return;
    }
    sessionStorage.setItem("respuesta_morosidad", respuesta);
    router.push("/loading-screen");
  };

  return (
    <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-xs font-medium mb-6">
            Paso 7 de 7
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
            Última pregunta
          </h1>
          <p className="text-[var(--muted-foreground)] text-sm">
            Tu respuesta es completamente anónima y confidencial.
          </p>
        </div>

        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-8 shadow-sm">
          <div className="mb-6 p-4 rounded-xl bg-[var(--accent)] border border-[var(--border)]">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--accent-foreground)]">
                  <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <p className="text-xs text-[var(--accent-foreground)] font-medium leading-relaxed">
                Esta pregunta es 100% anónima. Tu respuesta nunca será asociada a tu identidad ni compartida con terceros.
              </p>
            </div>
          </div>

          <p className="text-base text-[var(--foreground)] font-medium leading-relaxed mb-6">
            En los últimos 12 meses, ¿te has retrasado más de 30 días en el pago de alguna obligación (tarjeta, préstamo, cuota de estudios o recibo de servicios)?
          </p>

          <div className="space-y-3">
            {OPCIONES_MOROSIDAD.map((opcion) => {
              const seleccionado = respuesta === opcion.value;
              return (
                <button
                  key={opcion.value}
                  onClick={() => {
                    setRespuesta(opcion.value);
                    setError("");
                  }}
                  className={`w-full text-left p-4 rounded-xl border transition-all text-sm ${
                    seleccionado
                      ? "bg-[var(--accent)] border-[var(--primary)] text-[var(--foreground)]"
                      : "bg-[var(--card)] border-[var(--border)] text-[var(--foreground)] hover:border-[var(--primary)]"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`flex-shrink-0 mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                        seleccionado
                          ? "border-[var(--primary)] bg-[var(--primary)]"
                          : "border-[var(--border)] bg-transparent"
                      }`}
                    >
                      {seleccionado && (
                        <div className="w-2 h-2 rounded-full bg-[var(--primary-foreground)]" />
                      )}
                    </div>
                    <span className="leading-relaxed">{opcion.label}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {error && (
            <div className="mt-6 p-3 rounded-xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900">
              <p className="text-sm text-red-700 dark:text-red-300 text-center">{error}</p>
            </div>
          )}

          <div className="mt-8 flex gap-3">
            <button
              onClick={() => router.push("/evaluacion/pilar4")}
              className="flex-1 bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] font-medium py-3.5 rounded-xl transition-colors duration-150 text-sm"
            >
              Volver
            </button>
            <button
              onClick={handleContinuar}
              className="flex-[2] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
            >
              Finalizar encuesta
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
          Tus respuestas se guardan automáticamente
        </p>
      </div>
    </main>
  );
}
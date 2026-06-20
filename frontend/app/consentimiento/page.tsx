"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Consentimiento() {
  const router = useRouter();
  const [aceptado, setAceptado] = useState(false);

  const handleContinuar = () => {
    if (aceptado) {
      router.push("/datos");
    }
  };

  return (
    <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-xs font-medium mb-6">
            Paso 1 de 7
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
            Consentimiento informado
          </h1>
          <p className="text-[var(--muted-foreground)] text-sm">
            Por favor, lee la siguiente información antes de continuar.
          </p>
        </div>

        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-8 shadow-sm">
          <div className="space-y-5 text-sm text-[var(--foreground)] leading-relaxed">
            <p>
              Comprendo que este es un estudio académico anónimo realizado como parte de una tesis de ingeniería en SENATI.
            </p>
            <p>
              Acepto que mis respuestas sean procesadas estadísticamente con fines de investigación, sin que mi identidad sea revelada en ningún reporte o publicación derivada de este estudio.
            </p>
            <p>
              Entiendo que mi participación es voluntaria y que puedo abandonar la encuesta en cualquier momento sin consecuencia alguna.
            </p>
          </div>

          <div className="mt-8 p-4 rounded-xl bg-[var(--muted)] border border-[var(--border)]">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={aceptado}
                onChange={(e) => setAceptado(e.target.checked)}
                className="mt-0.5 w-5 h-5 rounded border-[var(--border)] text-[var(--primary)] focus:ring-[var(--ring)] cursor-pointer accent-[var(--primary)]"
              />
              <span className="text-sm text-[var(--foreground)] font-medium select-none">
                Sí, acepto participar en este estudio académico anónimo.
              </span>
            </label>
          </div>

          <div className="mt-8 flex gap-3">
            <button
              onClick={() => router.push("/")}
              className="flex-1 bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] font-medium py-3.5 rounded-xl transition-colors duration-150 text-sm"
            >
              Volver
            </button>
            <button
              onClick={handleContinuar}
              disabled={!aceptado}
              className="flex-[2] bg-[var(--primary)] hover:bg-[var(--primary-hover)] disabled:bg-[var(--muted)] disabled:text-[var(--muted-foreground)] disabled:cursor-not-allowed text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
            >
              Continuar
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
          Tus datos serán tratados con confidencialidad
        </p>
      </div>
    </main>
  );
}
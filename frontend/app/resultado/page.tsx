"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PredictResponse } from "../../lib/api";

export default function Resultado() {
  const router = useRouter();
  const [resultado, setResultado] = useState<PredictResponse | null>(null);
  const [nombre, setNombre] = useState("");
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const resultadoRaw = sessionStorage.getItem("resultado");
    const nombreRaw = sessionStorage.getItem("nombre_usuario");

    if (!resultadoRaw) {
      router.push("/");
      return;
    }

    setResultado(JSON.parse(resultadoRaw));
    setNombre(nombreRaw || "");
    setCargando(false);
  }, [router]);

  const limpiarSesion = () => {
    sessionStorage.clear();
    router.push("/");
  };

  if (cargando || !resultado) {
    return (
      <main className="min-h-screen bg-[var(--background)] flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-[var(--muted)] border-t-[var(--primary)] animate-spin" />
      </main>
    );
  }

  const prob = resultado.Probabilidad;
  const monto = resultado.Monto;
  const esPreAprobado = monto > 0;

  const primerNombre = nombre.split(" ")[0] || "";

  if (!esPreAprobado) {
    return (
      <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-xl">
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-10 shadow-sm text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--accent)] flex items-center justify-center">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--accent-foreground)]">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>

            <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
              {primerNombre ? `Gracias, ${primerNombre}` : "Gracias por tu participación"}
            </h1>
            <p className="text-[var(--muted-foreground)] text-sm leading-relaxed mb-8">
              Hemos registrado exitosamente tus respuestas. Tu colaboración es muy valiosa para esta investigación académica.
            </p>

            <div className="p-4 rounded-xl bg-[var(--muted)] border border-[var(--border)] mb-8">
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed">
                Los datos recolectados serán procesados estadísticamente con fines de investigación. Tu identidad permanecerá anónima en todos los reportes derivados de este estudio.
              </p>
            </div>

            <button
              onClick={limpiarSesion}
              className="w-full bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
            >
              Finalizar
            </button>
          </div>

          <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
            Proyecto de Grado · SENATI 2026
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-xs font-medium mb-6">
            Evaluación completada
          </div>
        </div>

        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-8 shadow-sm">
          <div className="text-center mb-6">
            <div className="w-16 h-16 mx-auto mb-5 rounded-full bg-[var(--accent)] flex items-center justify-center">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--accent-foreground)]">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] mb-2 tracking-tight">
              {primerNombre ? `¡Felicitaciones, ${primerNombre}!` : "¡Felicitaciones!"}
            </h1>
            <p className="text-[var(--muted-foreground)] text-sm leading-relaxed">
              Basándonos en el análisis de tu perfil, has sido <strong className="text-[var(--foreground)]">pre-aprobado</strong> para una oferta especial.
            </p>
          </div>

          <div className="my-8 p-6 rounded-2xl bg-[var(--accent)] border border-[var(--border)]">
            <p className="text-xs text-[var(--accent-foreground)] uppercase tracking-wider font-semibold mb-2 text-center">
              Monto pre-aprobado
            </p>
            <div className="text-center">
              <p className="text-4xl md:text-5xl font-bold text-[var(--foreground)] tracking-tight">
                S/ {monto.toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>

          <div className="space-y-3 mb-8 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-[var(--accent-foreground)]">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <span className="text-[var(--muted-foreground)] leading-relaxed">
                Esta es una oferta preliminar sujeta a evaluación final
              </span>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-[var(--accent-foreground)]">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <span className="text-[var(--muted-foreground)] leading-relaxed">
                Un asesor especializado se pondrá en contacto contigo
              </span>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-[var(--accent-foreground)]">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <span className="text-[var(--muted-foreground)] leading-relaxed">
                Tu información permanece protegida en todo momento
              </span>
            </div>
          </div>

          <button
            onClick={limpiarSesion}
            className="w-full bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
          >
            Finalizar
          </button>

          <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
            Ref: {(prob * 1000000).toFixed(0).padStart(7, "0")}
          </p>
        </div>

        <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
          Proyecto de Grado · SENATI 2026
        </p>
      </div>
    </main>
  );
}
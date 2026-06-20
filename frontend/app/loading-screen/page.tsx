"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { predict, UserInfo } from "../../lib/api";

const MENSAJES_ANIMACION = [
  "Procesando tus respuestas...",
  "Analizando patrones de comportamiento...",
  "Evaluando indicadores conductuales...",
  "Generando informe final...",
];

export default function LoadingScreen() {
  const router = useRouter();
  const [mensajeIdx, setMensajeIdx] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const procesamientoIniciado = useRef(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setMensajeIdx((prev) => (prev + 1) % MENSAJES_ANIMACION.length);
    }, 1200);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (procesamientoIniciado.current) return;
    procesamientoIniciado.current = true;

    const procesar = async () => {
      try {
        const userInfoRaw = sessionStorage.getItem("user_info");
        const pilar1Raw = sessionStorage.getItem("respuestas_pilar1");
        const pilar2Raw = sessionStorage.getItem("respuestas_pilar2");
        const pilar3Raw = sessionStorage.getItem("respuestas_pilar3");
        const pilar4Raw = sessionStorage.getItem("respuestas_pilar4");
        const morosidadRaw = sessionStorage.getItem("respuesta_morosidad");

        if (!userInfoRaw || !pilar1Raw || !pilar2Raw || !pilar3Raw || !pilar4Raw || !morosidadRaw) {
          throw new Error("Faltan datos de la encuesta. Por favor reinicia el proceso.");
        }

        const userInfo: UserInfo = JSON.parse(userInfoRaw);
        const pilar1: Record<string, string> = JSON.parse(pilar1Raw);
        const pilar2: Record<string, string> = JSON.parse(pilar2Raw);
        const pilar3: Record<string, string> = JSON.parse(pilar3Raw);
        const pilar4: Record<string, string> = JSON.parse(pilar4Raw);
        const morosidad = morosidadRaw;

        const ahora = new Date();
        const marcaTemporal = `${ahora.getFullYear()}/${String(ahora.getMonth() + 1).padStart(2, "0")}/${String(ahora.getDate()).padStart(2, "0")} ${String(ahora.getHours()).padStart(2, "0")}:${String(ahora.getMinutes()).padStart(2, "0")}:${String(ahora.getSeconds()).padStart(2, "0")}`;

        const respuestasCompletas: Record<string, string> = {
          "Marca temporal": marcaTemporal,
          Consentimiento: "Acepto",
          "DISTRITO DE RESIDENCIA": userInfo.distrito,
          "NIVEL EDUCATIVO": userInfo.nivel_educativo,
          ...pilar1,
          ...pilar2,
          ...pilar3,
          ...pilar4,
          "(Pregunta 100% ANÓNIMA): En los últimos 12 meses, ¿te has retrasado más de 30 días en el pago de alguna obligación (tarjeta, préstamo, cuota de estudios, o recibo de servicios)?": morosidad,
        };

        const tiempoMinimo = new Promise((resolve) => setTimeout(resolve, 4500));
        const [response] = await Promise.all([
          predict(respuestasCompletas, userInfo),
          tiempoMinimo,
        ]);

        sessionStorage.setItem("resultado", JSON.stringify(response));
        sessionStorage.setItem("nombre_usuario", userInfo.nombre);
        router.push("/resultado");
      } catch (err) {
        const mensaje = err instanceof Error ? err.message : "Ocurrió un error inesperado.";
        setErrorMsg(mensaje);
      }
    };

    procesar();
  }, [router]);

  if (errorMsg) {
    return (
      <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4">
        <div className="w-full max-w-md bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-8 shadow-sm text-center">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-950 flex items-center justify-center">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-600 dark:text-red-400">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-[var(--foreground)] mb-2">
            No pudimos procesar tu encuesta
          </h2>
          <p className="text-sm text-[var(--muted-foreground)] mb-6 leading-relaxed">
            {errorMsg}
          </p>
          <button
            onClick={() => router.push("/")}
            className="w-full bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3 rounded-xl transition-colors duration-150 text-sm"
          >
            Volver al inicio
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div className="relative w-20 h-20 mx-auto mb-8">
          <div className="absolute inset-0 rounded-full border-4 border-[var(--muted)]"></div>
          <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-[var(--primary)] animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--primary)]">
              <path d="M21 12c.552 0 1.005-.449.95-.998a10 10 0 1 0-9.952 10.948c.55.055.999-.398.999-.95V19a2 2 0 0 1 2-2h2a4 4 0 0 0 4-4z" />
              <circle cx="7" cy="11" r="1" />
              <circle cx="11" cy="7" r="1" />
              <circle cx="15" cy="9" r="1" />
              <circle cx="17" cy="13" r="1" />
            </svg>
          </div>
        </div>

        <h1 className="text-2xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
          Estamos procesando tu encuesta
        </h1>

        <div className="h-6 mb-8">
          <p
            key={mensajeIdx}
            className="text-sm text-[var(--muted-foreground)] animate-fade-in"
          >
            {MENSAJES_ANIMACION[mensajeIdx]}
          </p>
        </div>

        <div className="flex justify-center gap-2">
          {MENSAJES_ANIMACION.map((_, idx) => (
            <div
              key={idx}
              className={`h-1.5 rounded-full transition-all duration-500 ${
                idx === mensajeIdx
                  ? "w-8 bg-[var(--primary)]"
                  : "w-1.5 bg-[var(--muted)]"
              }`}
            />
          ))}
        </div>

        <p className="text-xs text-[var(--muted-foreground)] mt-12">
          Por favor no cierres esta ventana
        </p>
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.4s ease-out;
        }
      `}</style>
    </main>
  );
}
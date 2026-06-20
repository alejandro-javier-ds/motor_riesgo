"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

const PREGUNTAS_PILAR_2 = [
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [A menudo actúo por impulso en el momento y luego me arrepiento de las consecuencias.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Prefiero sacrificar mi tiempo libre hoy si sé que eso me traerá un gran beneficio el próximo año.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Cuando me encuentro con un problema difícil o tedioso, mi primer instinto es abandonarlo y hacer otra cosa.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Me cuesta mucho resistirme a mis antojos del momento, aunque sepa que después me arrepentiré.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Si me dan a elegir, prefiero esperar un mes por una recompensa excelente que recibir una recompensa regular hoy mismo.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Me aburro rápido de los pasatiempos o proyectos nuevos y salto a otra cosa rápidamente.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Siempre evalúo los pros y contras antes de tomar una decisión importante en mi vida diaria.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Si veo algo que me gusta mucho, busco la forma de tenerlo inmediatamente sin pensar mucho en el futuro.]",
];

const OPCIONES_LIKERT = [
  { value: "Totalmente en desacuerdo", label: "Totalmente en desacuerdo", short: "TD" },
  { value: "En desacuerdo", label: "En desacuerdo", short: "D" },
  { value: "Neutral", label: "Neutral", short: "N" },
  { value: "De acuerdo", label: "De acuerdo", short: "A" },
  { value: "Totalmente de acuerdo", label: "Totalmente de acuerdo", short: "TA" },
];

function extraerAfirmacion(pregunta: string): string {
  const match = pregunta.match(/\[(.*?)\]/);
  return match ? match[1] : pregunta;
}

export default function Pilar2() {
  const router = useRouter();
  const [respuestas, setRespuestas] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    const saved = sessionStorage.getItem("respuestas_pilar2");
    if (saved) setRespuestas(JSON.parse(saved));
  }, []);

  const handleSeleccionar = (pregunta: string, valor: string) => {
    const nuevas = { ...respuestas, [pregunta]: valor };
    setRespuestas(nuevas);
    setError("");
  };

  const handleContinuar = () => {
    const sinResponder = PREGUNTAS_PILAR_2.filter((p) => !respuestas[p]);
    if (sinResponder.length > 0) {
      setError(`Te faltan ${sinResponder.length} pregunta${sinResponder.length > 1 ? "s" : ""} por responder.`);
      return;
    }
    sessionStorage.setItem("respuestas_pilar2", JSON.stringify(respuestas));
    router.push("/evaluacion/pilar3");
  };

  const respondidas = Object.keys(respuestas).length;
  const progreso = (respondidas / PREGUNTAS_PILAR_2.length) * 100;

  return (
    <main className="min-h-screen bg-[var(--background)] flex justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-xs font-medium mb-6">
            Paso 4 de 7
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
            Bloque 2 de 4
          </h1>
          <p className="text-[var(--muted-foreground)] text-sm">
            Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas.
          </p>
        </div>

        <div className="mb-6 bg-[var(--card)] border border-[var(--card-border)] rounded-xl px-5 py-3 shadow-sm">
          <div className="flex items-center justify-between text-xs text-[var(--muted-foreground)] mb-2">
            <span>Progreso del bloque</span>
            <span className="font-semibold text-[var(--foreground)]">
              {respondidas} / {PREGUNTAS_PILAR_2.length}
            </span>
          </div>
          <div className="h-1.5 w-full bg-[var(--muted)] rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--primary)] rounded-full transition-all duration-300"
              style={{ width: `${progreso}%` }}
            />
          </div>
        </div>

        <div className="space-y-4">
          {PREGUNTAS_PILAR_2.map((pregunta, idx) => (
            <div
              key={pregunta}
              className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-6 shadow-sm"
            >
              <div className="flex items-start gap-3 mb-5">
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] flex items-center justify-center text-xs font-bold">
                  {idx + 1}
                </div>
                <p className="text-sm md:text-base text-[var(--foreground)] font-medium leading-relaxed">
                  {extraerAfirmacion(pregunta)}
                </p>
              </div>

              <div className="grid grid-cols-5 gap-2">
                {OPCIONES_LIKERT.map((opcion) => {
                  const seleccionado = respuestas[pregunta] === opcion.value;
                  return (
                    <button
                      key={opcion.value}
                      onClick={() => handleSeleccionar(pregunta, opcion.value)}
                      className={`flex flex-col items-center justify-center gap-1.5 py-3 px-2 rounded-xl border transition-all text-xs ${
                        seleccionado
                          ? "bg-[var(--primary)] border-[var(--primary)] text-[var(--primary-foreground)] shadow-sm"
                          : "bg-[var(--card)] border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--primary)] hover:text-[var(--foreground)]"
                      }`}
                    >
                      <span className={`text-base font-bold ${seleccionado ? "text-[var(--primary-foreground)]" : "text-[var(--foreground)]"}`}>
                        {opcion.short}
                      </span>
                      <span className="text-[10px] leading-tight text-center hidden md:block">
                        {opcion.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {error && (
          <div className="mt-6 p-3 rounded-xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900">
            <p className="text-sm text-red-700 dark:text-red-300 text-center">{error}</p>
          </div>
        )}

        <div className="mt-8 flex gap-3">
          <button
            onClick={() => router.push("/evaluacion/pilar1")}
            className="flex-1 bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] font-medium py-3.5 rounded-xl transition-colors duration-150 text-sm"
          >
            Volver
          </button>
          <button
            onClick={handleContinuar}
            className="flex-[2] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
          >
            Continuar al bloque 3
          </button>
        </div>

        <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
          Tus respuestas se guardan automáticamente
        </p>
      </div>
    </main>
  );
}
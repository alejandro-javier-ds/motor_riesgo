"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

const PREGUNTAS_PILAR_1 = [
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Mi espacio de trabajo y mi habitación suelen estar siempre ordenados.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Prefiero terminar mis obligaciones urgentes antes de sentarme a relajarme o salir.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Me genera mucha ansiedad la idea de llegar tarde a un compromiso, aunque sea una reunión informal.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Me molesta profundamente cuando las personas cambian los planes a última hora sin avisar.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Suelo revisar dos o tres veces los mensajes o correos importantes antes de enviarlos.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Cuando empiezo un proyecto personal o tarea en casa, lo termino aunque me tome más tiempo del planeado.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Llevo un registro mental o escrito de las tareas que debo hacer durante la semana.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [A menudo dejo las cosas en cualquier lado y luego pierdo tiempo buscándolas.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Siento que es mi obligación cumplir con una promesa, incluso si la otra persona ya lo olvidó.]",
  "Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas. [Frecuentemente postergo tareas aburridas hasta el último minuto posible.]",
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

export default function Pilar1() {
  const router = useRouter();
  const [respuestas, setRespuestas] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    const saved = sessionStorage.getItem("respuestas_pilar1");
    if (saved) setRespuestas(JSON.parse(saved));
  }, []);

  const handleSeleccionar = (pregunta: string, valor: string) => {
    const nuevas = { ...respuestas, [pregunta]: valor };
    setRespuestas(nuevas);
    setError("");
  };

  const handleContinuar = () => {
    const sinResponder = PREGUNTAS_PILAR_1.filter((p) => !respuestas[p]);
    if (sinResponder.length > 0) {
      setError(`Te faltan ${sinResponder.length} pregunta${sinResponder.length > 1 ? "s" : ""} por responder.`);
      return;
    }
    sessionStorage.setItem("respuestas_pilar1", JSON.stringify(respuestas));
    router.push("/evaluacion/pilar2");
  };

  const respondidas = Object.keys(respuestas).length;
  const progreso = (respondidas / PREGUNTAS_PILAR_1.length) * 100;

  return (
    <main className="min-h-screen bg-[var(--background)] flex justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-xs font-medium mb-6">
            Paso 3 de 7
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
            Bloque 1 de 4
          </h1>
          <p className="text-[var(--muted-foreground)] text-sm">
            Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas.
          </p>
        </div>

        <div className="mb-6 bg-[var(--card)] border border-[var(--card-border)] rounded-xl px-5 py-3 shadow-sm">
          <div className="flex items-center justify-between text-xs text-[var(--muted-foreground)] mb-2">
            <span>Progreso del bloque</span>
            <span className="font-semibold text-[var(--foreground)]">
              {respondidas} / {PREGUNTAS_PILAR_1.length}
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
          {PREGUNTAS_PILAR_1.map((pregunta, idx) => (
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
            onClick={() => router.push("/datos")}
            className="flex-1 bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] font-medium py-3.5 rounded-xl transition-colors duration-150 text-sm"
          >
            Volver
          </button>
          <button
            onClick={handleContinuar}
            className="flex-[2] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
          >
            Continuar al bloque 2
          </button>
        </div>

        <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
          Tus respuestas se guardan automáticamente
        </p>
      </div>
    </main>
  );
}
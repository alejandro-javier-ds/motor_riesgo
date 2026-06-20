"use client";

import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-xs font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-[var(--primary)]"></span>
            Investigación académica · SENATI 2026
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
            Estudio sobre Patrones de Toma de Decisiones Cotidianas
          </h1>
          <p className="text-[var(--muted-foreground)] text-base">
            Tu opinión nos ayuda a entender cómo las personas toman decisiones en el día a día.
          </p>
        </div>

        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-8 shadow-sm">
          <div className="space-y-6">
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-[var(--foreground)]">
                Antes de comenzar
              </h2>
              <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
                Este formulario evalúa cómo reaccionas a situaciones cotidianas. No hay respuestas correctas ni incorrectas — solo nos interesa tu perspectiva honesta.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3 py-4 border-y border-[var(--border)]">
              <div className="text-center">
                <div className="text-xl font-bold text-[var(--foreground)]">30</div>
                <div className="text-xs text-[var(--muted-foreground)] mt-1">Preguntas</div>
              </div>
              <div className="text-center border-x border-[var(--border)]">
                <div className="text-xl font-bold text-[var(--foreground)]">4 min</div>
                <div className="text-xs text-[var(--muted-foreground)] mt-1">Duración</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-[var(--foreground)]">100%</div>
                <div className="text-xs text-[var(--muted-foreground)] mt-1">Anónimo</div>
              </div>
            </div>

            <div className="space-y-3 text-sm text-[var(--muted-foreground)]">
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-[var(--accent-foreground)]">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <span>Tus respuestas serán procesadas estadísticamente</span>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-[var(--accent-foreground)]">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <span>No se solicitan datos sensibles ni de contacto</span>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-[var(--accent-foreground)]">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <span>Uso exclusivamente académico</span>
              </div>
            </div>

            <button
              onClick={() => router.push("/consentimiento")}
              className="w-full bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
            >
              Comenzar encuesta
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
          Proyecto de Grado · Ingeniería de Ciencia de Datos e IA
        </p>
      </div>
    </main>
  );
}
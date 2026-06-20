"use client";

import { useState } from "react";
import { getAdminData, AdminResultado } from "../../lib/api";

export default function Admin() {
  const [password, setPassword] = useState("");
  const [autenticado, setAutenticado] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [resultados, setResultados] = useState<AdminResultado[]>([]);
  const [registroSeleccionado, setRegistroSeleccionado] = useState<AdminResultado | null>(null);

  const handleLogin = async () => {
    if (!password.trim()) {
      setError("Ingresa la contraseña");
      return;
    }
    setError("");
    setCargando(true);
    try {
      const data = await getAdminData(password);
      setResultados(data.resultados);
      setAutenticado(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setCargando(false);
    }
  };

  const handleRefresh = async () => {
    setCargando(true);
    try {
      const data = await getAdminData(password);
      setResultados(data.resultados);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setCargando(false);
    }
  };

  const formatearFecha = (fecha: string) => {
    const d = new Date(fecha);
    return d.toLocaleString("es-PE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const limpiarFeatureName = (feature: string): string => {
    const match = feature.match(/\[(.*?)\]/);
    if (match) return match[1];
    if (feature.includes("Pregunta 100% ANÓNIMA")) return "Historial de morosidad (12 meses)";
    if (feature.includes("DISTRITO")) return "Distrito de residencia";
    if (feature.includes("NIVEL EDUCATIVO")) return "Nivel educativo";
    if (feature === "Marca temporal") return "Marca temporal";
    if (feature === "Consentimiento") return "Consentimiento";
    return feature;
  };

  if (!autenticado) {
    return (
      <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-[var(--primary)] flex items-center justify-center">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--primary-foreground)]">
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-[var(--foreground)] tracking-tight">Panel administrativo</h1>
            <p className="text-sm text-[var(--muted-foreground)] mt-2">Acceso restringido a personal autorizado</p>
          </div>

          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-8 shadow-sm">
            <label className="block text-sm font-medium text-[var(--foreground)] mb-2">Contraseña de acceso</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              placeholder="Ingresa la contraseña"
              className="w-full px-4 py-3 rounded-xl bg-[var(--input)] border border-[var(--border)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:border-transparent transition-all text-sm"
            />

            {error && (
              <div className="mt-4 p-3 rounded-xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900">
                <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
              </div>
            )}

            <button
              onClick={handleLogin}
              disabled={cargando}
              className="mt-6 w-full bg-[var(--primary)] hover:bg-[var(--primary-hover)] disabled:opacity-60 disabled:cursor-not-allowed text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
            >
              {cargando ? "Verificando..." : "Acceder"}
            </button>
          </div>

          <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
            Sustentación de tesis · SENATI 2026
          </p>
        </div>
      </main>
    );
  }

  const stats = {
    total: resultados.length,
    preAprobados: resultados.filter((r) => r.monto_aprobado > 0).length,
    denegados: resultados.filter((r) => r.monto_aprobado === 0).length,
    probPromedio: resultados.length > 0
      ? (resultados.reduce((acc, r) => acc + r.probabilidad_viabilidad, 0) / resultados.length)
      : 0,
  };

  return (
    <main className="min-h-screen bg-[var(--background)] px-4 py-8 md:px-8 md:py-12">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] tracking-tight">
              Panel administrativo
            </h1>
            <p className="text-sm text-[var(--muted-foreground)] mt-1">
              Motor Predictivo de Riesgo Conductual · Tesis SENATI 2026
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={cargando}
            className="px-4 py-2.5 bg-[var(--card)] border border-[var(--border)] hover:bg-[var(--muted)] text-[var(--foreground)] rounded-xl text-sm font-medium transition-colors disabled:opacity-60 flex items-center gap-2 self-start"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
            </svg>
            {cargando ? "Actualizando..." : "Actualizar"}
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-5 shadow-sm">
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider font-medium mb-2">Total</p>
            <p className="text-3xl font-bold text-[var(--foreground)]">{stats.total}</p>
            <p className="text-xs text-[var(--muted-foreground)] mt-1">Evaluaciones</p>
          </div>
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-5 shadow-sm">
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider font-medium mb-2">Pre-aprobados</p>
            <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{stats.preAprobados}</p>
            <p className="text-xs text-[var(--muted-foreground)] mt-1">{stats.total > 0 ? ((stats.preAprobados / stats.total) * 100).toFixed(0) : 0}% del total</p>
          </div>
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-5 shadow-sm">
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider font-medium mb-2">Denegados</p>
            <p className="text-3xl font-bold text-red-600 dark:text-red-400">{stats.denegados}</p>
            <p className="text-xs text-[var(--muted-foreground)] mt-1">{stats.total > 0 ? ((stats.denegados / stats.total) * 100).toFixed(0) : 0}% del total</p>
          </div>
          <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-5 shadow-sm">
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider font-medium mb-2">Prob. promedio</p>
            <p className="text-3xl font-bold text-[var(--foreground)]">{(stats.probPromedio * 100).toFixed(1)}%</p>
            <p className="text-xs text-[var(--muted-foreground)] mt-1">Riesgo conductual</p>
          </div>
        </div>

        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-[var(--border)]">
            <h2 className="text-lg font-semibold text-[var(--foreground)]">Últimas evaluaciones</h2>
            <p className="text-xs text-[var(--muted-foreground)] mt-1">Click sobre un registro para ver su análisis SHAP</p>
          </div>

          {resultados.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-sm text-[var(--muted-foreground)]">No hay evaluaciones registradas todavía.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-[var(--muted)] text-[var(--muted-foreground)]">
                  <tr>
                    <th className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wider">Nombre</th>
                    <th className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wider">Edad</th>
                    <th className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wider">Distrito</th>
                    <th className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wider">Prob.</th>
                    <th className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wider">Decisión</th>
                    <th className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wider">Monto</th>
                    <th className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wider">Fecha</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {resultados.map((r, idx) => (
                    <tr
                      key={idx}
                      onClick={() => setRegistroSeleccionado(r)}
                      className="cursor-pointer hover:bg-[var(--muted)] transition-colors"
                    >
                      <td className="px-6 py-4 font-medium text-[var(--foreground)]">{r.nombre_completo || "—"}</td>
                      <td className="px-6 py-4 text-[var(--muted-foreground)]">{r.edad}</td>
                      <td className="px-6 py-4 text-[var(--muted-foreground)]">{r.distrito_residencia}</td>
                      <td className="px-6 py-4">
                        <span className="font-mono text-[var(--foreground)]">{(r.probabilidad_viabilidad * 100).toFixed(1)}%</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
                          r.monto_aprobado > 0
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400"
                            : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400"
                        }`}>
                          {r.estado_final}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-[var(--foreground)]">
                        {r.monto_aprobado > 0 ? `S/ ${r.monto_aprobado.toFixed(2)}` : "—"}
                      </td>
                      <td className="px-6 py-4 text-xs text-[var(--muted-foreground)]">{formatearFecha(r.fecha_registro)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {registroSeleccionado && (
          <div
            onClick={() => setRegistroSeleccionado(null)}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl shadow-xl max-w-3xl w-full my-8 max-h-[90vh] overflow-y-auto"
            >
              <div className="sticky top-0 bg-[var(--card)] border-b border-[var(--border)] px-6 py-4 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-[var(--foreground)]">Análisis SHAP individual</h3>
                  <p className="text-xs text-[var(--muted-foreground)] mt-0.5">{registroSeleccionado.nombre_completo || "Usuario anónimo"}</p>
                </div>
                <button
                  onClick={() => setRegistroSeleccionado(null)}
                  className="w-8 h-8 rounded-lg hover:bg-[var(--muted)] flex items-center justify-center text-[var(--muted-foreground)] transition-colors"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>

              <div className="p-6 space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 rounded-xl bg-[var(--muted)] border border-[var(--border)]">
                    <p className="text-[10px] text-[var(--muted-foreground)] uppercase tracking-wider font-medium">Edad</p>
                    <p className="text-sm font-semibold text-[var(--foreground)] mt-1">{registroSeleccionado.edad} años</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--muted)] border border-[var(--border)]">
                    <p className="text-[10px] text-[var(--muted-foreground)] uppercase tracking-wider font-medium">Probabilidad</p>
                    <p className="text-sm font-semibold text-[var(--foreground)] mt-1 font-mono">{(registroSeleccionado.probabilidad_viabilidad * 100).toFixed(2)}%</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--muted)] border border-[var(--border)]">
                    <p className="text-[10px] text-[var(--muted-foreground)] uppercase tracking-wider font-medium">Decisión</p>
                    <p className="text-sm font-semibold text-[var(--foreground)] mt-1">{registroSeleccionado.estado_final}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--muted)] border border-[var(--border)]">
                    <p className="text-[10px] text-[var(--muted-foreground)] uppercase tracking-wider font-medium">Monto</p>
                    <p className="text-sm font-semibold text-[var(--foreground)] mt-1 font-mono">
                      {registroSeleccionado.monto_aprobado > 0 ? `S/ ${registroSeleccionado.monto_aprobado.toFixed(2)}` : "—"}
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-[var(--foreground)] mb-3">Top 10 features que influyeron en la decisión</h4>
                  <p className="text-xs text-[var(--muted-foreground)] mb-4 leading-relaxed">
                    Valores positivos (rojo) empujan hacia mayor riesgo de morosidad. Valores negativos (verde) empujan hacia menor riesgo.
                  </p>

                  {registroSeleccionado.shap_explicacion && registroSeleccionado.shap_explicacion.top_features.length > 0 ? (
                    <div className="space-y-2">
                      {registroSeleccionado.shap_explicacion.top_features.map((f, idx) => {
                        const esPositivo = f.shap_value > 0;
                        const maxAbs = Math.max(...registroSeleccionado.shap_explicacion!.top_features.map((x) => Math.abs(x.shap_value)));
                        const width = (Math.abs(f.shap_value) / maxAbs) * 100;
                        return (
                          <div key={idx} className="p-3 rounded-xl bg-[var(--muted)] border border-[var(--border)]">
                            <div className="flex items-start justify-between gap-3 mb-2">
                              <p className="text-xs font-medium text-[var(--foreground)] flex-1 leading-snug">
                                {limpiarFeatureName(f.feature)}
                              </p>
                              <span className={`text-xs font-mono font-semibold flex-shrink-0 ${
                                esPositivo ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                              }`}>
                                {esPositivo ? "+" : ""}{f.shap_value.toFixed(4)}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-[var(--background)] rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${esPositivo ? "bg-red-500" : "bg-emerald-500"} transition-all`}
                                  style={{ width: `${width}%` }}
                                />
                              </div>
                              <span className="text-[10px] text-[var(--muted-foreground)] font-mono w-16 text-right truncate" title={f.input_value}>
                                {f.input_value.length > 12 ? f.input_value.substring(0, 12) + "..." : f.input_value}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-[var(--muted-foreground)] text-center py-8">
                      No hay datos SHAP disponibles para este registro.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
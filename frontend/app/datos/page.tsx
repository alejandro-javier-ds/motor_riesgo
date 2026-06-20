"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const DISTRITOS_LIMA = [
  "Ancón", "Ate", "Barranco", "Breña", "Carabayllo", "Cercado de Lima",
  "Chaclacayo", "Chorrillos", "Cieneguilla", "Comas", "El Agustino",
  "Independencia", "Jesús María", "La Molina", "La Victoria", "Lince",
  "Los Olivos", "Lurigancho-Chosica", "Lurín", "Magdalena del Mar",
  "Miraflores", "Pachacámac", "Pucusana", "Pueblo Libre", "Puente Piedra",
  "Punta Hermosa", "Punta Negra", "Rímac", "San Bartolo", "San Borja",
  "San Isidro", "San Juan de Lurigancho", "San Juan de Miraflores",
  "San Luis", "San Martín de Porres", "San Miguel", "Santa Anita",
  "Santa María del Mar", "Santa Rosa", "Santiago de Surco", "Surquillo",
  "Villa El Salvador", "Villa María del Triunfo",
];

const NIVELES_EDUCATIVOS = [
  "Sin educación formal", "Primaria Incompleta", "Primaria Completa",
  "Secundaria Incompleta", "Secundaria Completa",
  "Instituto Técnico Incompleto / En curso", "Instituto Técnico Completo",
  "Escuela de Educación Superior Incompleta / En curso",
  "Escuela de Educación Superior Completa",
  "Universitaria Incompleta / En curso", "Universitaria Completa",
  "Bachiller", "Titulado", "Maestría", "Doctorado",
];

const SITUACIONES_LABORALES = [
  "Desempleado", "Trabajo del hogar no remunerado", "Estudiante",
  "Trabajo eventual", "Independiente Informal", "Independiente Formal",
  "Dueño de negocio", "Dependiente Formal", "Docente",
];

export default function Datos() {
  const router = useRouter();
  const [nombre, setNombre] = useState("");
  const [edad, setEdad] = useState("");
  const [distrito, setDistrito] = useState("");
  const [nivelEducativo, setNivelEducativo] = useState("");
  const [situacionLaboral, setSituacionLaboral] = useState("");
  const [error, setError] = useState("");

  const handleContinuar = () => {
    if (!nombre.trim()) {
      setError("Por favor ingresa tu nombre completo.");
      return;
    }
    const edadNum = parseInt(edad);
    if (!edad || isNaN(edadNum) || edadNum < 15 || edadNum > 80) {
      setError("Ingresa una edad válida (entre 15 y 80 años).");
      return;
    }
    if (!distrito) {
      setError("Selecciona tu distrito de residencia.");
      return;
    }
    if (!nivelEducativo) {
      setError("Selecciona tu nivel educativo.");
      return;
    }
    if (!situacionLaboral) {
      setError("Selecciona tu situación laboral.");
      return;
    }

    const datos = {
      nombre: nombre.trim(),
      edad: edadNum,
      distrito,
      nivel_educativo: nivelEducativo,
      situacion_laboral: situacionLaboral,
    };

    sessionStorage.setItem("user_info", JSON.stringify(datos));
    router.push("/evaluacion/pilar1");
  };

  return (
    <main className="min-h-screen bg-[var(--background)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-xs font-medium mb-6">
            Paso 2 de 7
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--foreground)] mb-3 tracking-tight">
            Información general
          </h1>
          <p className="text-[var(--muted-foreground)] text-sm">
            Necesitamos algunos datos básicos antes de comenzar.
          </p>
        </div>

        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-8 shadow-sm">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-[var(--foreground)] mb-2">
                Nombre completo
              </label>
              <input
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ej: Juan Pérez García"
                className="w-full px-4 py-3 rounded-xl bg-[var(--input)] border border-[var(--border)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:border-transparent transition-all text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--foreground)] mb-2">
                Edad
              </label>
              <input
                type="number"
                value={edad}
                onChange={(e) => setEdad(e.target.value)}
                min={15}
                max={80}
                placeholder="Ej: 25"
                className="w-full px-4 py-3 rounded-xl bg-[var(--input)] border border-[var(--border)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:border-transparent transition-all text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--foreground)] mb-2">
                Distrito de residencia
              </label>
              <select
                value={distrito}
                onChange={(e) => setDistrito(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-[var(--input)] border border-[var(--border)] text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:border-transparent transition-all text-sm appearance-none cursor-pointer"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 1rem center",
                  paddingRight: "2.5rem",
                }}
              >
                <option value="">Selecciona tu distrito</option>
                {DISTRITOS_LIMA.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--foreground)] mb-2">
                Nivel educativo
              </label>
              <select
                value={nivelEducativo}
                onChange={(e) => setNivelEducativo(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-[var(--input)] border border-[var(--border)] text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:border-transparent transition-all text-sm appearance-none cursor-pointer"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 1rem center",
                  paddingRight: "2.5rem",
                }}
              >
                <option value="">Selecciona tu nivel educativo</option>
                {NIVELES_EDUCATIVOS.map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--foreground)] mb-2">
                Situación laboral
              </label>
              <select
                value={situacionLaboral}
                onChange={(e) => setSituacionLaboral(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-[var(--input)] border border-[var(--border)] text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:border-transparent transition-all text-sm appearance-none cursor-pointer"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 1rem center",
                  paddingRight: "2.5rem",
                }}
              >
                <option value="">Selecciona tu situación laboral</option>
                {SITUACIONES_LABORALES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900">
                <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => router.push("/consentimiento")}
                className="flex-1 bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] font-medium py-3.5 rounded-xl transition-colors duration-150 text-sm"
              >
                Volver
              </button>
              <button
                onClick={handleContinuar}
                className="flex-[2] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--primary-foreground)] font-semibold py-3.5 rounded-xl transition-colors duration-150 text-sm tracking-wide"
              >
                Continuar
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-[var(--muted-foreground)] mt-6">
          Estos datos son anónimos y de uso exclusivamente académico
        </p>
      </div>
    </main>
  );
}
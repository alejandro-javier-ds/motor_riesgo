const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UserInfo {
  nombre: string;
  edad: number;
  distrito: string;
  nivel_educativo: string;
  situacion_laboral: string;
}

export interface PredictRequest {
  data: Record<string, string[]>;
  user_info: Record<string, string | number>;
}

export interface PredictResponse {
  Decision: string;
  Monto: number;
  Probabilidad: number;
}

export interface ShapFeature {
  feature: string;
  shap_value: number;
  input_value: string;
}

export interface ShapExplicacion {
  base_value: number;
  top_features: ShapFeature[];
}

export interface AdminResultado {
  nombre_completo: string;
  edad: number;
  distrito_residencia: string;
  nivel_educativo: string;
  situacion_laboral: string;
  fecha_registro: string;
  probabilidad_viabilidad: number;
  estado_final: string;
  monto_aprobado: number;
  shap_explicacion: ShapExplicacion | null;
}

export interface AdminResponse {
  total: number;
  resultados: AdminResultado[];
}

export async function predict(
  respuestas: Record<string, string>,
  userInfo: UserInfo
): Promise<PredictResponse> {
  const data: Record<string, string[]> = {};
  for (const [key, value] of Object.entries(respuestas)) {
    data[key] = [value];
  }

  const body: PredictRequest = {
    data,
    user_info: {
      nombre: userInfo.nombre,
      edad: userInfo.edad,
      distrito: userInfo.distrito,
      nivel_educativo: userInfo.nivel_educativo,
      situacion_laboral: userInfo.situacion_laboral,
    },
  };

  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Error en el servidor");
  }

  return res.json();
}

export async function getAdminData(password: string): Promise<AdminResponse> {
  const res = await fetch(`${API_URL}/admin/resultados`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Password": password,
    },
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new Error("Contraseña incorrecta");
    }
    const error = await res.json();
    throw new Error(error.detail || "Error al obtener datos");
  }

  return res.json();
}
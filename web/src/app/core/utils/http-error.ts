import { HttpErrorResponse } from '@angular/common/http';

/**
 * Extrae y normaliza un mensaje de error legible a partir de una respuesta de error HTTP (HttpErrorResponse o similar),
 * formateando adecuadamente los errores de validación de Pydantic/FastAPI (HTTP 422) donde `detail`
 * se entrega como un arreglo de objetos [{loc: [...], msg: "...", type: "..."}], evitando la renderización
 * de `[object Object]` en la interfaz de usuario.
 */
export function extractErrorMessage(error: unknown, fallback: string = 'Error inesperado en el servidor'): string {
  if (!error) {
    return fallback;
  }

  // Si es directamente un string
  if (typeof error === 'string') {
    return error.trim() || fallback;
  }

  const httpErr = error as HttpErrorResponse | { error?: unknown; status?: number; message?: string };

  // Error de conexión / red
  if (httpErr.status === 0) {
    return 'Error de comunicación con el servidor. Verifique la conexión de red.';
  }

  const payload = httpErr.error;

  // Si el cuerpo del error es un string directo (ej. texto plano devuelto por proxy/servidor)
  if (typeof payload === 'string' && payload.trim().length > 0) {
    return payload;
  }

  // Si el cuerpo del error es un objeto JSON estructurado
  if (payload && typeof payload === 'object') {
    const detail = (payload as { detail?: unknown }).detail;

    // 1. detail como string (ej. HTTPException estándar de FastAPI: detail="Mensaje")
    if (typeof detail === 'string' && detail.trim().length > 0) {
      return detail;
    }

    // 2. detail como arreglo de errores de validación (Pydantic / FastAPI 422 Unprocessable Entity)
    if (Array.isArray(detail) && detail.length > 0) {
      const messages = detail
        .map((item) => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object') {
            const locList = Array.isArray((item as { loc?: unknown[] }).loc)
              ? (item as { loc: unknown[] }).loc.filter((p) => p !== 'body')
              : [];
            const loc = locList.join('.');
            const msg = (item as { msg?: string; message?: string }).msg || (item as { message?: string }).message;

            if (loc && msg) {
              return `${loc}: ${msg}`;
            }
            return msg || JSON.stringify(item);
          }
          return String(item);
        })
        .filter(Boolean);

      if (messages.length > 0) {
        return messages.join('. ');
      }
    }

    // 3. Fallback a propiedad message estándar
    const message = (payload as { message?: unknown }).message;
    if (typeof message === 'string' && message.trim().length > 0) {
      return message;
    }
  }

  // 4. Fallback a message del HttpErrorResponse
  if (typeof httpErr.message === 'string' && httpErr.message.trim().length > 0) {
    return httpErr.message;
  }

  return fallback;
}


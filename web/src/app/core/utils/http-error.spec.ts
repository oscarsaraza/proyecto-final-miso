import { HttpErrorResponse } from '@angular/common/http';
import { extractErrorMessage } from './http-error';

describe('extractErrorMessage', () => {
  it('devuelve el fallback si el error es null o undefined', () => {
    expect(extractErrorMessage(null, 'Fallback')).toBe('Fallback');
    expect(extractErrorMessage(undefined, 'Fallback')).toBe('Fallback');
  });

  it('devuelve el string directamente si se pasa un string', () => {
    expect(extractErrorMessage('Error directo', 'Fallback')).toBe('Error directo');
  });

  it('devuelve mensaje de conexión si el status es 0', () => {
    const error = new HttpErrorResponse({ status: 0 });
    expect(extractErrorMessage(error, 'Fallback')).toBe(
      'Error de comunicación con el servidor. Verifique la conexión de red.',
    );
  });

  it('extrae detail cuando es un string estándar de FastAPI (400, 404, 500)', () => {
    const error = new HttpErrorResponse({
      status: 400,
      error: { detail: 'El solicitante tiene 17 años. No es asegurable.' },
    });
    expect(extractErrorMessage(error, 'Fallback')).toBe(
      'El solicitante tiene 17 años. No es asegurable.',
    );
  });

  it('formatea correctamente un error 422 de FastAPI donde detail es un arreglo de objetos de Pydantic', () => {
    const error = new HttpErrorResponse({
      status: 422,
      error: {
        detail: [
          {
            loc: ['body', 'birth_date'],
            msg: 'Formato de fecha inválido. Se espera AAAA-MM-DD',
            type: 'value_error',
          },
          {
            loc: ['body', 'insured_amount'],
            msg: 'El monto asegurado debe ser mayor a 0',
            type: 'greater_than',
          },
        ],
      },
    });

    const result = extractErrorMessage(error, 'Fallback');
    expect(result).toBe(
      'birth_date: Formato de fecha inválido. Se espera AAAA-MM-DD. insured_amount: El monto asegurado debe ser mayor a 0',
    );
    expect(result).not.toContain('[object Object]');
  });

  it('formatea elementos de detail cuando son strings planos', () => {
    const error = new HttpErrorResponse({
      status: 422,
      error: {
        detail: ['Campo obligatorio faltante', 'Valor fuera de rango'],
      },
    });
    expect(extractErrorMessage(error, 'Fallback')).toBe(
      'Campo obligatorio faltante. Valor fuera de rango',
    );
  });

  it('extrae el payload de texto plano si error es un string no-JSON', () => {
    const error = new HttpErrorResponse({
      status: 502,
      error: 'Bad Gateway: Nginx upstream down',
    });
    expect(extractErrorMessage(error, 'Fallback')).toBe('Bad Gateway: Nginx upstream down');
  });

  it('utiliza la propiedad message si no hay detail', () => {
    const error = new HttpErrorResponse({
      status: 500,
      error: { message: 'Fallo interno no controlado' },
    });
    expect(extractErrorMessage(error, 'Fallback')).toBe('Fallo interno no controlado');
  });
});


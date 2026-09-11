import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

const respuestasDegradadas = new Rate('respuestas_degradadas');

export const options = {
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'max'],
  scenarios: {
    cotizaciones: {
      executor: 'shared-iterations',
      vus: 10,
      iterations: Number(__ENV.ITERACIONES || 100),
      maxDuration: '5m',
    },
  },
};

export default function () {
  const carga = JSON.stringify({
    clienteId: `CLI-00${(__ITER % 3) + 1}`,
    monto: 250000,
    edad: 35,
  });

  const res = http.post('http://api:8000/api/v1/quotes', carga, {
    headers: { 'Content-Type': 'application/json' },
  });

  const cuerpo = res.json();
  respuestasDegradadas.add(cuerpo && cuerpo.status === 'degraded');

  check(res, {
    'responde 200': (r) => r.status === 200,
    'incluye prima': () => cuerpo && typeof cuerpo.prima === 'number',
  });
}

export function handleSummary(data) {
  const destino = `/salida/${__ENV.NOMBRE_SALIDA || 'resumen'}.json`;
  return { [destino]: JSON.stringify(data, null, 2), stdout: '' };
}

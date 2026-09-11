import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const porReplica = new Counter('peticiones_por_replica');

export const options = {
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'max'],
  scenarios: {
    carga_constante: {
      executor: 'constant-arrival-rate',
      rate: 50,
      timeUnit: '1s',
      duration: '3m',
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
};

export default function () {
  const res = http.post(
    'http://nginx:80/api/v1/quotes',
    JSON.stringify({ clienteId: 'CLI-001', monto: 250000, edad: 35 }),
    { headers: { 'Content-Type': 'application/json' } },
  );

  check(res, { 'responde 200': (r) => r.status === 200 });

  if (res.status === 200) {
    const cuerpo = res.json();
    if (cuerpo && cuerpo.replica) porReplica.add(1, { replica: cuerpo.replica });
  }
}

export function handleSummary(data) {
  const destino = `/salida/${__ENV.NOMBRE_SALIDA || 'resumen'}.json`;
  return { [destino]: JSON.stringify(data, null, 2), stdout: '' };
}

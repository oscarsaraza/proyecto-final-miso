/** Pesos colombianos sin centavos, como en el prototipo. */
export const COP = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
});

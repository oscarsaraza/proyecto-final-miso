/* ============================================================================
   Solventa · Catálogo de Iconos SVG Vectoriales (Móvil)
   Trazo de 1.75px sobre rejilla de 24x24 con soporte de tamaño dinámico
   ========================================================================= */

const svg = (d, tam = 20) =>
  `<svg class="icono" width="${tam}" height="${tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;

const ICONOS = {
  escudo: (t) => svg('<path d="M12 3l7 3v6c0 4.2-2.9 7.8-7 9-4.1-1.2-7-4.8-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/>', t),
  sol: (t) => svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/>', t),
  luna: (t) => svg('<path d="M20 14.5A8.5 8.5 0 019.5 4a8.5 8.5 0 1010.5 10.5z"/>', t),
  monitor: (t) => svg('<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>', t),
  movil: (t) => svg('<rect x="7" y="2" width="10" height="20" rx="2.5"/><path d="M11 18.5h2"/>', t),
  info: (t) => svg('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>', t),
  check: (t) => svg('<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>', t),
  alerta: (t) => svg('<path d="M10.3 4.3L2.6 17.5A2 2 0 004.3 20.5h15.4a2 2 0 001.7-3L13.7 4.3a2 2 0 00-3.4 0z"/><path d="M12 9v4M12 16.5h.01"/>', t),
  equis: (t) => svg('<circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/>', t),
  globo: (t) => svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 010 18 15 15 0 010-18z"/>', t),
  mapa: (t) => svg('<path d="M12 21s7-6.3 7-11a7 7 0 10-14 0c0 4.7 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>', t),
  accesible: (t) => svg('<circle cx="12" cy="5" r="2"/><path d="M5 8.5l7 1.5 7-1.5M12 10v5M12 15l-3 6M12 15l3 6"/>', t),
  camara: (t) => svg('<path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 011 1v9a1 1 0 01-1 1H4a1 1 0 01-1-1V9a1 1 0 011-1z"/><circle cx="12" cy="13" r="3.5"/>', t),
  sinSenal: (t) => svg('<path d="M2 3l20 18M8.5 15.5a5 5 0 016.2-.6M5 12a10 10 0 013-1.9M12 19h.01"/>', t),
  huella: (t) => svg('<path d="M12 4a8 8 0 018 8v2M4 12a8 8 0 014-6.9M8 20a12 12 0 001.5-6 2.5 2.5 0 015 0c0 2-.3 3.8-.9 5.4M12 11.5v3"/>', t),
  reloj: (t) => svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', t),
  documento: (t) => svg('<path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>', t),
  buscar: (t) => svg('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>', t),
  tarjeta: (t) => svg('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h3"/>', t),
  enchufe: (t) => svg('<path d="M9 3v6M15 3v6M6 9h12v3a6 6 0 01-12 0V9zM12 18v3"/>', t),
  cartera: (t) => svg('<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M16 14.5h2"/>', t),
  llave: (t) => svg('<circle cx="8" cy="12" r="4"/><path d="M12 12h9M18 12v3M15 12v2"/>', t),
  candado: (t) => svg('<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 118 0v3"/>', t),
  flechaDerecha: (t) => svg('<path d="M5 12h14M12 5l7 7-7 7"/>', t),
  flechaIzquierda: (t) => svg('<path d="M19 12H5M12 19l-7-7 7-7"/>', t),
  refrescar: (t) => svg('<path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>', t),
  rayo: (t) => svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>', t),
  usuario: (t) => svg('<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>', t),
  ajustes: (t) => svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>', t),
  wifi: (t) => svg('<path d="M5 12.55a11 11 0 0114.08 0M1.42 9a16 16 0 0121.16 0M8.53 16.11a6 6 0 016.95 0M12 20h.01"/>', t),
};

if (typeof window !== 'undefined') {
  window.ICONOS = ICONOS;
}

/* Iconos SVG en línea, trazo de 1,75 px sobre rejilla de 24. */
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
};

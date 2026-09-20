/* ============================================================================
   Solventa · Barra y Panel Flotante de Control de Demostración (Web)
   Permite forzar escenarios de resiliencia y ver la sincronización en vivo.
   ========================================================================= */

function inicializarControlDemoWeb(appState, alCambiarEstado) {
  const contenedor = document.createElement('div');
  contenedor.className = 'demo-widget';
  contenedor.id = 'demoWidget';

  contenedor.innerHTML = `
    <div class="demo-panel" id="demoPanel">
      <h4>
        <span>⚙️ ${window.t('demoTitulo', appState.idioma)}</span>
        <span style="font-size:10px;color:#38bdf8;font-weight:normal;">v1.0</span>
      </h4>
      <p>${window.t('demoDesc', appState.idioma)}</p>
      
      <div class="sync-status-indicator">
        <span class="sync-dot"></span>
        <span>${window.t('sincronizadoOk', appState.idioma)}</span>
      </div>

      <button type="button" class="demo-btn-accion" id="btnToggleDegradado">
        <span>⚡ ${window.t('modoDegradado', appState.idioma)}</span>
        <span id="badgeDegradado" class="chip neutro">OFF</span>
      </button>

      <button type="button" class="demo-btn-accion" id="btnToggleRechazo">
        <span>🚫 ${window.t('modoRechazo', appState.idioma)}</span>
        <span id="badgeRechazo" class="chip neutro">OFF</span>
      </button>

      <button type="button" class="demo-btn-accion" id="btnAvanzarSiniestro">
        <span>📋 ${window.t('avanzarSiniestro', appState.idioma)}</span>
        <span>&rarr;</span>
      </button>

      <button type="button" class="demo-btn-accion" id="btnResetDemo" style="margin-top:4px;border-color:rgba(244,63,94,0.3);color:#fda4af;">
        <span>🔄 ${window.t('resetDatos', appState.idioma)}</span>
      </button>
    </div>

    <button type="button" class="demo-btn-toggle" id="btnDemoToggle" aria-label="Abrir panel de control de demostración">
      <span>⚙️ PoC Demo</span>
      <span class="chip ok" style="padding:1px 6px;font-size:10px;">LIVE</span>
    </button>
  `;

  document.body.appendChild(contenedor);

  const panel = document.getElementById('demoPanel');
  const btnToggle = document.getElementById('btnDemoToggle');
  const btnDegradado = document.getElementById('btnToggleDegradado');
  const btnRechazo = document.getElementById('btnToggleRechazo');
  const btnAvanzar = document.getElementById('btnAvanzarSiniestro');
  const btnReset = document.getElementById('btnResetDemo');

  const badgeDeg = document.getElementById('badgeDegradado');
  const badgeRec = document.getElementById('badgeRechazo');

  function actualizarBadges() {
    const config = window.SolventaDB.getDemoConfig();
    if (config.modoDegradadoForzado) {
      btnDegradado.classList.add('activo');
      badgeDeg.textContent = 'ON';
      badgeDeg.className = 'chip aviso';
    } else {
      btnDegradado.classList.remove('activo');
      badgeDeg.textContent = 'OFF';
      badgeDeg.className = 'chip neutro';
    }

    if (config.modoRechazoForzado) {
      btnRechazo.classList.add('activo');
      badgeRec.textContent = 'ON';
      badgeRec.className = 'chip error';
    } else {
      btnRechazo.classList.remove('activo');
      badgeRec.textContent = 'OFF';
      badgeRec.className = 'chip neutro';
    }
  }

  btnToggle.addEventListener('click', () => {
    panel.classList.toggle('abierto');
  });

  btnDegradado.addEventListener('click', () => {
    const config = window.SolventaDB.getDemoConfig();
    window.SolventaDB.setDemoConfig('modoDegradadoForzado', !config.modoDegradadoForzado);
    actualizarBadges();
    if (alCambiarEstado) alCambiarEstado();
  });

  btnRechazo.addEventListener('click', () => {
    const config = window.SolventaDB.getDemoConfig();
    window.SolventaDB.setDemoConfig('modoRechazoForzado', !config.modoRechazoForzado);
    actualizarBadges();
    if (alCambiarEstado) alCambiarEstado();
  });

  btnAvanzar.addEventListener('click', () => {
    const siniestros = window.SolventaDB.getSiniestros();
    if (siniestros.length > 0) {
      window.SolventaDB.avanzarEstadoSiniestro(siniestros[0].id);
      if (alCambiarEstado) alCambiarEstado();
    }
  });

  btnReset.addEventListener('click', () => {
    if (confirm('¿Desea restablecer los datos de demostración a su estado de fábrica?')) {
      window.SolventaDB.resetToDefaults();
      actualizarBadges();
      if (alCambiarEstado) alCambiarEstado();
    }
  });

  actualizarBadges();
}

if (typeof window !== 'undefined') {
  window.inicializarControlDemoWeb = inicializarControlDemoWeb;
}

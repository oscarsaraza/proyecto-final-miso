/* ============================================================================
   Solventa · Control de Demostración (Móvil)
   Permite alternar entre estado Online / Offline, forzar sincronizaciones
   y avanzar el estado del siniestro en la línea de tiempo.
   ========================================================================= */

function inicializarControlDemoMovil(appState, alCambiarEstado) {
  const contenedor = document.createElement('div');
  contenedor.className = 'demo-widget-movil';
  contenedor.id = 'demoWidgetMovil';

  contenedor.innerHTML = `
    <div class="demo-panel-movil" id="demoPanelMovil">
      <h4>
        <span>⚙️ ${window.t('demoTitulo', appState.idioma)}</span>
        <span style="font-size:9px;color:#38bdf8;">MÓVIL</span>
      </h4>
      <p style="font-size:10px;color:#94a3b8;margin:0;">${window.t('demoDesc', appState.idioma)}</p>

      <button type="button" class="demo-btn-movil-accion" id="btnToggleOfflineMovil">
        <span>📶 Simular Modo Offline</span>
        <span id="badgeOfflineMovil" class="chip neutro" style="font-size:10px;padding:2px 6px;">ONLINE</span>
      </button>

      <button type="button" class="demo-btn-movil-accion" id="btnSyncColaMovil">
        <span>🔄 Sincronizar cola offline</span>
        <span id="badgeCountCola" class="chip aviso" style="font-size:10px;padding:2px 6px;">0</span>
      </button>

      <button type="button" class="demo-btn-movil-accion" id="btnAvanzarSiniestroMovil">
        <span>📋 Avanzar estado siniestro</span>
        <span>&rarr;</span>
      </button>

      <button type="button" class="demo-btn-movil-accion" id="btnResetDemoMovil" style="margin-top:2px;border-color:rgba(244,63,94,0.3);color:#fda4af;">
        <span>🔄 Restablecer datos</span>
      </button>
    </div>

    <button type="button" class="demo-btn-movil" id="btnDemoToggleMovil" aria-label="Abrir panel de control de demostración">
      <span>⚙️ PoC</span>
      <span class="chip ok" id="indicadorRedPill" style="padding:1px 5px;font-size:9px;">ON</span>
    </button>
  `;

  document.body.appendChild(contenedor);

  const panel = document.getElementById('demoPanelMovil');
  const btnToggle = document.getElementById('btnDemoToggleMovil');
  const btnOffline = document.getElementById('btnToggleOfflineMovil');
  const btnSync = document.getElementById('btnSyncColaMovil');
  const btnAvanzar = document.getElementById('btnAvanzarSiniestroMovil');
  const btnReset = document.getElementById('btnResetDemoMovil');

  const badgeOff = document.getElementById('badgeOfflineMovil');
  const badgeCola = document.getElementById('badgeCountCola');
  const pillRed = document.getElementById('indicadorRedPill');

  function actualizar() {
    const config = window.SolventaDB.getDemoConfig();
    const cola = window.SolventaDB.getColaOffline();

    if (config.modoOfflineSimulado) {
      badgeOff.textContent = 'OFFLINE';
      badgeOff.className = 'chip aviso';
      pillRed.textContent = 'OFF';
      pillRed.className = 'chip aviso';
      document.getElementById('bannerOffline')?.classList.add('visible');
    } else {
      badgeOff.textContent = 'ONLINE';
      badgeOff.className = 'chip ok';
      pillRed.textContent = 'ON';
      pillRed.className = 'chip ok';
      document.getElementById('bannerOffline')?.classList.remove('visible');
    }

    badgeCola.textContent = cola.length;
    badgeCola.style.display = cola.length > 0 ? 'inline-block' : 'none';
  }

  btnToggle.addEventListener('click', () => {
    panel.classList.toggle('abierto');
  });

  btnOffline.addEventListener('click', () => {
    const config = window.SolventaDB.getDemoConfig();
    const nuevo = !config.modoOfflineSimulado;
    window.SolventaDB.setDemoConfig('modoOfflineSimulado', nuevo);
    actualizar();
    if (alCambiarEstado) alCambiarEstado();
  });

  btnSync.addEventListener('click', () => {
    const radicados = window.SolventaDB.sincronizarColaOffline();
    if (radicados.length > 0) {
      alert(`¡Sincronización completada! Se radicaron ${radicados.length} siniestros.`);
    } else {
      alert('La cola de sincronización está vacía.');
    }
    actualizar();
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
    if (confirm('¿Restablecer datos demo móviles a su estado de fábrica?')) {
      window.SolventaDB.resetToDefaults();
      actualizar();
      if (alCambiarEstado) alCambiarEstado();
    }
  });

  actualizar();
}

if (typeof window !== 'undefined') {
  window.inicializarControlDemoMovil = inicializarControlDemoMovil;
}

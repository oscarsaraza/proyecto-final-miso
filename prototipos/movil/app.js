/* ============================================================================
   Solventa · Prototipo Móvil Ejecutable (Validación de Interfaz con Usuario Final)
   Flujo interactivo con autenticación biométrica y alternativa simuladas,
   carné digital 3D interactivo, reporte de siniestros y resiliencia offline.
   ========================================================================= */

(function () {
  const urlParams = new URLSearchParams(window.location.search);

  const state = {
    // Autenticación simulada: inicia en false (pantalla de bloqueo/biometría)
    autenticado: window.sessionStorage.getItem('solventa_movil_auth') === 'true',
    vistaActual: urlParams.get('vista') || 'billetera', // 'billetera', 'siniestros', 'cuenta', 'biometria', 'loginAlt'
    idioma: ['es', 'en'].includes(urlParams.get('idioma')) ? urlParams.get('idioma') : 'es',
    region: ['CO', 'MX', 'CL', 'PE'].includes(urlParams.get('region')) ? urlParams.get('region') : 'CO',
    tema: urlParams.get('tema') === 'oscuro' ? 'oscuro' : 'claro',

    carneVolteado: false,

    // Asistente de siniestro
    reporte: {
      paso: 1, // 1: Evidencia, 2: Detalle, 3: Confirmación
      fotoSeleccionada: 'foto1',
      polizaId: 'POL-2026-004182',
      ubicacion: '4.6512, −74.0568 · Cra. 7 # 71-21, Bogotá',
      descripcion: 'Impacto lateral en puerta del conductor con desprendimiento parcial de lámina.',
      siniestroActivoId: 'SIN-2026-00871',
      itemEncoladoId: null,
    },
  };

  const tr = (k) => window.t(k, state.idioma);
  const fmtMoneda = (val) => window.formatoDinero(val, state.region);
  const fmtFecha = (iso) => window.formatoFecha(iso, state.region);

  // --- Renderizado de Cabecera Móvil y Barra de Estado ---
  function renderCabecera() {
    document.documentElement.lang = state.idioma;
    document.documentElement.dataset.tema = state.tema;

    const selIdioma = document.getElementById('selIdiomaMovil');
    const selRegion = document.getElementById('selRegionMovil');
    const btnTema = document.getElementById('btnTemaMovil');
    const tabbar = document.querySelector('.tabbar-movil');

    if (selIdioma) selIdioma.value = state.idioma;
    if (selRegion) {
      selRegion.innerHTML = Object.entries(window.REGIONES)
        .map(([c, r]) => `<option value="${c}" ${c === state.region ? 'selected' : ''}>${c} (${r.moneda})</option>`)
        .join('');
    }
    if (btnTema) {
      btnTema.innerHTML = state.tema === 'oscuro' ? window.ICONOS.sol(16) : window.ICONOS.luna(16);
    }

    // El TabBar solo se muestra cuando el usuario está autenticado
    if (tabbar) {
      if (!state.autenticado) {
        tabbar.classList.add('oculto');
      } else {
        tabbar.classList.remove('oculto');
        document.querySelectorAll('.tab-item-movil').forEach((btn) => {
          const v = btn.dataset.vista;
          btn.classList.toggle('activo', v === state.vistaActual);
        });
      }
    }

    // Control de conexión simulada (en barra de estado)
    const config = window.SolventaDB.getDemoConfig();
    const esOffline = !!config.modoOfflineSimulado;
    const banner = document.getElementById('bannerOffline');
    if (banner) {
      banner.classList.toggle('visible', esOffline);
    }

    const estadoIconos = document.querySelector('.barra-estado-iconos');
    if (estadoIconos) {
      estadoIconos.style.cursor = 'pointer';
      estadoIconos.title = 'Clic para alternar conexión Online / Offline (Demo)';
      estadoIconos.innerHTML = esOffline
        ? `<span style="color:var(--aviso);">${window.ICONOS.sinSenal(14)} Sin señal</span>`
        : `<span>${window.ICONOS.wifi(14)} 4G</span> <span>82%</span>`;
    }
  }

  // --- Vista M1: Acceso Biométrico ---
  function renderBiometria() {
    return `
      <div style="text-align:center;padding:var(--e5) 0 var(--e3);">
        <span class="simbolo-mini" style="width:52px;height:52px;border-radius:15px;display:inline-grid;place-items:center;background:linear-gradient(135deg,var(--marca-500),var(--acento));color:#fff;margin-bottom:var(--e3);">
          ${window.ICONOS.escudo(28)}
        </span>
        <h2 style="font-size:var(--t-xl);margin-bottom:var(--e1);">${tr('accesoBiometrico')}</h2>
        <p style="color:var(--texto-sec);font-size:var(--t-sm);margin:0;">${tr('toqueSensor')}</p>
      </div>

      <div class="sensor-area">
        <button type="button" class="sensor-boton" id="btnSensorBiometrico" aria-label="${tr('toqueSensor')}">
          ${window.ICONOS.huella(56)}
        </button>
        <strong id="sensorFeedback" style="font-size:var(--t-sm);color:var(--primario);">${tr('sensorListo')}</strong>
      </div>

      <button type="button" class="btn-movil btn-movil-secundario" id="btnIrLoginAlt">
        ${tr('usarAlternativo')}
      </button>

      <p style="text-align:center;font-size:11px;color:var(--texto-sec);margin-top:var(--e5);">
        ${window.ICONOS.candado(12)} ${tr('cifradoDispositivo')}
      </p>
    `;
  }

  // --- Vista M2: Acceso Alternativo ---
  function renderLoginAlternativo() {
    return `
      <div style="padding:var(--e4) 0;">
        <h2 style="font-size:var(--t-lg);margin-bottom:var(--e1);">${tr('accesoAlternativo')}</h2>
        <p style="color:var(--texto-sec);font-size:var(--t-sm);margin:0 0 var(--e4);">${tr('accesoAltDesc')}</p>

        <div style="display:flex;flex-direction:column;gap:var(--e3);margin-bottom:var(--e5);">
          <div>
            <label style="font-size:11px;font-weight:700;color:var(--texto-sec);text-transform:uppercase;">${tr('correo')}</label>
            <input type="email" value="maria.ruiz@correo.co" style="width:100%;height:44px;border:1px solid var(--borde);border-radius:var(--r-sm);padding:0 var(--e3);font-size:var(--t-sm);background:var(--superficie);color:var(--texto);">
          </div>
          <div>
            <label style="font-size:11px;font-weight:700;color:var(--texto-sec);text-transform:uppercase;">${tr('clave')}</label>
            <input type="password" value="••••••••" style="width:100%;height:44px;border:1px solid var(--borde);border-radius:var(--r-sm);padding:0 var(--e3);font-size:var(--t-sm);background:var(--superficie);color:var(--texto);">
          </div>
          <div>
            <label style="font-size:11px;font-weight:700;color:var(--texto-sec);text-transform:uppercase;">${tr('codigoOtp')}</label>
            <div style="display:flex;gap:var(--e2);">
              <input type="text" id="inpOtpMovil" value="417902" style="flex:1;height:44px;border:1px solid var(--borde);border-radius:var(--r-sm);padding:0 var(--e3);font-size:var(--t-md);font-weight:700;letter-spacing:.1em;background:var(--superficie);color:var(--texto);">
              <button type="button" class="btn-movil btn-movil-secundario" id="btnAutollenarOtpMovil" style="width:auto;font-size:11px;white-space:nowrap;">
                Demo SMS
              </button>
            </div>
            <span style="font-size:11px;color:var(--texto-sec);margin-top:4px;display:block;">${tr('reenviarEn')} 00:42</span>
          </div>
        </div>

        <button type="button" class="btn-movil btn-movil-primario" id="btnEntrarLoginAlt" style="margin-bottom:var(--e3);">
          ${tr('btnEntrar')}
        </button>
        <button type="button" class="btn-movil btn-movil-secundario" id="btnVolverBiometria">
          ${tr('btnVolverBiometria')}
        </button>
      </div>
    `;
  }

  // --- Vista M3 / M4: Billetera de Pólizas (Carné 3D Interactivo) ---
  function renderBilletera() {
    const polizas = window.SolventaDB.getPolizas();
    const config = window.SolventaDB.getDemoConfig();
    const esOffline = config.modoOfflineSimulado;

    const polizaPrincipal = polizas[0] || {
      id: 'POL-2026-004182',
      ramoNombre: 'Vida Hipotecario',
      clienteNombre: 'María Fernanda Ruiz',
      montoAsegurado: 250000000,
      fechaVigencia: '2027-09-01T08:00:00',
    };

    return `
      <div>
        <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:var(--e2);">
          <div>
            <h2 style="font-size:var(--t-lg);">${tr('bienvenida')}</h2>
            <p style="font-size:var(--t-xs);color:var(--texto-sec);margin:0;">${tr('subtituloBienvenida')}</p>
          </div>
          ${
            esOffline
              ? `<span class="chip aviso" style="cursor:pointer;" id="toggleOnlinePill">${window.ICONOS.sinSenal(12)} ${tr('enCache')}</span>`
              : `<span class="chip ok" style="cursor:pointer;" id="toggleOfflinePill">${window.ICONOS.check(12)} En línea</span>`
          }
        </div>

        <!-- Carné Digital 3D -->
        <div class="carne-envoltorio" id="carneInteractivo" title="${tr('tocarGirar')}">
          <div class="carne-card ${state.carneVolteado ? 'volteada' : ''}">
            <!-- Frente del carné -->
            <div class="carne-cara carne-frente">
              <div class="carne-cabecera">
                <div class="logo-carne">
                  ${window.ICONOS.escudo(20)} Solventa
                </div>
                <div class="carne-ramo-chip">${polizaPrincipal.ramoNombre}</div>
              </div>

              <div>
                <div class="carne-numero">${polizaPrincipal.id}</div>
                <div style="font-size:var(--t-sm);font-weight:600;">${polizaPrincipal.clienteNombre}</div>
              </div>

              <div class="carne-pie">
                <div class="carne-dato">
                  <span>${tr('sumaAsegurada')}</span>
                  <strong>${fmtMoneda(polizaPrincipal.montoAsegurado)}</strong>
                </div>
                <div class="carne-dato" style="text-align:right;">
                  <span>${tr('vigenteHasta')}</span>
                  <strong>${fmtFecha(polizaPrincipal.fechaVigencia).split(',')[0]}</strong>
                </div>
              </div>
            </div>

            <!-- Dorso del carné (Coberturas) -->
            <div class="carne-cara carne-dorso">
              <div class="carne-cabecera">
                <strong style="font-size:var(--t-sm);">${tr('coberturasTitulo')}</strong>
                <span class="chip ok" style="font-size:10px;">${tr('estadoVigente')}</span>
              </div>
              <ul style="list-style:none;padding:0;margin:0;font-size:12px;line-height:1.6;">
                <li>✓ Fallecimiento por cualquier causa (100%)</li>
                <li>✓ Incapacidad total y permanente (100%)</li>
                <li>✓ Auxilio funerario inmediato</li>
                <li>✓ Asistencia médica de orientación telefónica</li>
              </ul>
              <div style="font-size:10px;opacity:0.75;text-align:center;">
                ${tr('tocarGirar')} &bull; Solventa Aseguradora S.A.
              </div>
            </div>
          </div>
        </div>

        <!-- Botón de acción principal -->
        <button type="button" class="btn-movil btn-movil-primario" id="btnAccionReportar" style="margin-bottom:var(--e4);">
          ${window.ICONOS.camara(20)} ${tr('reportarSiniestroBtn')}
        </button>

        <!-- Lista de pólizas -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--e2);">
          <h3 style="font-size:var(--t-sm);text-transform:uppercase;letter-spacing:.04em;color:var(--texto-sec);">${tr('misPolizas')}</h3>
          <span style="font-size:11px;color:var(--texto-sec);">${polizas.length} registradas</span>
        </div>

        <ul class="lista-movil">
          ${polizas
            .map(
              (p) => `
            <li class="lista-movil-item">
              <div class="icono-bolsa">${window.ICONOS.escudo(20)}</div>
              <div class="crece">
                <strong>${p.ramoNombre}</strong>
                <span>${p.id} &bull; ${fmtMoneda(p.montoAsegurado)}</span>
              </div>
              <span class="chip ${p.estado === 'vigente' ? 'ok' : p.estado === 'pendiente' ? 'neutro' : 'error'}">
                ${p.estado}
              </span>
            </li>
          `
            )
            .join('')}
        </ul>

        <p style="font-size:11px;color:var(--texto-sec);text-align:center;margin-top:var(--e5);">
          ${window.ICONOS.reloj(12)} ${tr('ultimaSync')}: ${fmtFecha(new Date().toISOString())}
        </p>
      </div>
    `;
  }

  // --- Vista M5 / M6 / M7: Flujo de Siniestros ---
  function renderSiniestros() {
    const siniestros = window.SolventaDB.getSiniestros();
    const cola = window.SolventaDB.getColaOffline();

    // Paso 1: Evidencia
    if (state.reporte.paso === 1) {
      return `
        <div>
          <div style="margin-bottom:var(--e3);">
            <h2 style="font-size:var(--t-lg);">${tr('reportarTitulo')}</h2>
            <p style="font-size:var(--t-xs);color:var(--texto-sec);margin:0;">${tr('paso1Evidencia')} &bull; Evidencia fotográfica</p>
          </div>

          <p style="font-size:var(--t-sm);margin:0 0 var(--e2);">${tr('seleccioneFoto')}</p>
          <div class="foto-selector-grid">
            <div class="foto-demo-card ${state.reporte.fotoSeleccionada === 'foto1' ? 'seleccionada' : ''}" data-select-foto="foto1">
              ${window.ICONOS.camara(24)}
              <span>${tr('foto1')}</span>
            </div>
            <div class="foto-demo-card ${state.reporte.fotoSeleccionada === 'foto2' ? 'seleccionada' : ''}" data-select-foto="foto2">
              ${window.ICONOS.camara(24)}
              <span>${tr('foto2')}</span>
            </div>
            <div class="foto-demo-card ${state.reporte.fotoSeleccionada === 'foto3' ? 'seleccionada' : ''}" data-select-foto="foto3">
              ${window.ICONOS.camara(24)}
              <span>${tr('foto3')}</span>
            </div>
          </div>

          <div style="background:var(--superficie-alt);border:1px solid var(--borde);border-radius:var(--r-md);padding:var(--e3);margin-bottom:var(--e4);">
            <div style="display:flex;align-items:center;gap:var(--e2);color:var(--ok);font-size:var(--t-xs);font-weight:700;">
              ${window.ICONOS.check(16)} Fotografía de evidencia cargada (1.8 MB)
            </div>
            <span style="font-size:11px;color:var(--texto-sec);margin-top:2px;display:block;">Geotag y fecha embebidos automáticamente</span>
          </div>

          <button type="button" class="btn-movil btn-movil-primario" id="btnPasoSiguiente">
            ${tr('btnSiguiente')} &rarr;
          </button>
        </div>
      `;
    }

    // Paso 2: Detalle
    if (state.reporte.paso === 2) {
      const polizas = window.SolventaDB.getPolizas();
      return `
        <div>
          <div style="margin-bottom:var(--e3);">
            <h2 style="font-size:var(--t-lg);">${tr('reportarTitulo')}</h2>
            <p style="font-size:var(--t-xs);color:var(--texto-sec);margin:0;">${tr('paso2Detalle')} &bull; Circunstancias y póliza</p>
          </div>

          <div style="display:flex;flex-direction:column;gap:var(--e3);margin-bottom:var(--e4);">
            <div>
              <label style="font-size:11px;font-weight:700;color:var(--texto-sec);text-transform:uppercase;">${tr('polizaAfectada')}</label>
              <select id="selPolizaAfectada" style="width:100%;height:44px;border:1px solid var(--borde);border-radius:var(--r-sm);padding:0 var(--e3);font-size:var(--t-sm);background:var(--superficie);color:var(--texto);">
                ${polizas.map((p) => `<option value="${p.id}" ${p.id === state.reporte.polizaId ? 'selected' : ''}>${p.ramoNombre} - ${p.id}</option>`).join('')}
              </select>
            </div>

            <div>
              <label style="font-size:11px;font-weight:700;color:var(--texto-sec);text-transform:uppercase;">${tr('ubicacionDetectada')}</label>
              <input type="text" value="${state.reporte.ubicacion}" readonly style="width:100%;height:44px;border:1px solid var(--borde);border-radius:var(--r-sm);padding:0 var(--e3);font-size:var(--t-xs);background:var(--superficie-alt);color:var(--texto);">
            </div>

            <div>
              <label style="font-size:11px;font-weight:700;color:var(--texto-sec);text-transform:uppercase;">${tr('fechaHoraIncidente')}</label>
              <input type="text" value="${fmtFecha(new Date().toISOString())}" readonly style="width:100%;height:44px;border:1px solid var(--borde);border-radius:var(--r-sm);padding:0 var(--e3);font-size:var(--t-xs);background:var(--superficie-alt);color:var(--texto);">
            </div>

            <div>
              <label style="font-size:11px;font-weight:700;color:var(--texto-sec);text-transform:uppercase;">${tr('descripcionHechos')}</label>
              <textarea id="txtDescSiniestro" rows="3" style="width:100%;border:1px solid var(--borde);border-radius:var(--r-sm);padding:var(--e2) var(--e3);font-family:inherit;font-size:var(--t-sm);background:var(--superficie);color:var(--texto);">${state.reporte.descripcion}</textarea>
            </div>
          </div>

          <div style="display:flex;gap:var(--e2);">
            <button type="button" class="btn-movil btn-movil-secundario" id="btnPasoAtras">
              &larr; ${tr('btnAtras')}
            </button>
            <button type="button" class="btn-movil btn-movil-primario" id="btnEnviarSiniestroFinal">
              ${tr('btnEnviarSiniestro')}
            </button>
          </div>
        </div>
      `;
    }

    // Pantalla M6: Confirmación de cola offline
    if (state.reporte.paso === 'offline_queue') {
      return `
        <div style="padding:var(--e2) 0;">
          <div class="aviso atencion" style="padding:var(--e4);flex-direction:column;align-items:flex-start;">
            <div style="display:flex;gap:var(--e2);align-items:center;">
              ${window.ICONOS.sinSenal(24)}
              <strong>${tr('enColaTitulo')}</strong>
            </div>
            <p style="margin:6px 0 0;font-size:var(--t-sm);">${tr('enColaDesc')}</p>
          </div>

          <div style="background:var(--superficie);border:1px solid var(--borde);border-radius:var(--r-md);padding:var(--e4);margin-bottom:var(--e4);">
            <span style="font-size:11px;color:var(--texto-sec);text-transform:uppercase;">${tr('radicadoProvisional')}</span>
            <div style="font-size:var(--t-lg);font-weight:800;color:var(--aviso);font-family:monospace;margin:4px 0;">
              ${state.reporte.itemEncoladoId || 'OFF-2026-9901'}
            </div>
            <p style="font-size:12px;color:var(--texto-sec);margin:0;">
              ${tr('garantiaIdempotencia')}
            </p>
          </div>

          <button type="button" class="btn-movil btn-movil-primario" id="btnVolverBilleteraDesdeCola">
            Volver a Billetera
          </button>
        </div>
      `;
    }

    // Pantalla M7: Seguimiento del siniestro radicado
    const siniestro =
      siniestros.find((s) => s.id === state.reporte.siniestroActivoId) || siniestros[0];

    return `
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--e3);">
          <h2 style="font-size:var(--t-lg);">${tr('radicadoTitulo')}</h2>
          <button type="button" class="btn-movil btn-movil-secundario" id="btnNuevoReporte" style="width:auto;min-height:34px;font-size:11px;padding:0 10px;">
            + Nuevo
          </button>
        </div>

        ${
          siniestro
            ? `
          <div style="background:linear-gradient(135deg,var(--primario-suave),var(--superficie));border:1px solid rgba(11,84,116,0.2);border-radius:var(--r-md);padding:var(--e4);margin-bottom:var(--e4);text-align:center;">
            <span style="font-size:11px;color:var(--texto-sec);text-transform:uppercase;">${tr('numRadicado')}</span>
            <div style="font-size:var(--t-xl);font-weight:800;color:var(--primario);font-family:monospace;margin:4px 0;">
              ${siniestro.id}
            </div>
            <span class="chip ${siniestro.estado === 'resuelto' ? 'ok' : 'aviso'}" style="margin-top:2px;">
              ${siniestro.estado}
            </span>
          </div>

          <h3 style="font-size:var(--t-sm);color:var(--texto-sec);text-transform:uppercase;letter-spacing:.04em;margin-bottom:var(--e2);">
            ${tr('lineaTiempo')}
          </h3>

          <ol class="linea-tiempo" style="margin-bottom:var(--e5);">
            <li class="hecho">
              <strong>${tr('etapaRecibido')}</strong>
              <span class="cuando">${fmtFecha(siniestro.fechaReporte)}</span>
            </li>
            <li class="${['asignado', 'enEvaluacion', 'resuelto'].includes(siniestro.estado) ? 'hecho' : 'actual'}">
              <strong>${tr('etapaAsignado')}</strong>
              <span class="cuando">${['asignado', 'enEvaluacion', 'resuelto'].includes(siniestro.estado) ? 'Perito asignado' : 'En proceso'}</span>
            </li>
            <li class="${['enEvaluacion', 'resuelto'].includes(siniestro.estado) ? (siniestro.estado === 'resuelto' ? 'hecho' : 'actual') : ''}">
              <strong>${tr('etapaEvaluacion')}</strong>
              <span class="cuando">${siniestro.estado === 'resuelto' ? 'Dictamen favorable emitido' : 'Revisión técnica de soportes'}</span>
            </li>
            <li class="${siniestro.estado === 'resuelto' ? 'hecho' : ''}">
              <strong>${tr('etapaResuelto')}</strong>
              <span class="cuando">${siniestro.estado === 'resuelto' ? 'Indemnización desembolsada' : 'Pendiente de cierre'}</span>
            </li>
          </ol>
        `
            : `
          <p style="color:var(--texto-sec);">${tr('sinSiniestros')}</p>
        `
        }

        ${
          cola.length > 0
            ? `
          <div class="aviso atencion" style="cursor:pointer;" id="avisoColaSyncClick">
            ${window.ICONOS.sinSenal(18)}
            <div>
              <strong>${cola.length} ${tr('pendienteSync')}</strong>
              <p style="margin:2px 0 0;font-size:11px;">Se enviarán en cuanto haya señal (toque para sincronizar ahora).</p>
            </div>
          </div>
        `
            : ''
        }
      </div>
    `;
  }

  // --- Vista Perfil / Mi Cuenta ---
  function renderCuenta() {
    const cliente = window.SolventaDB.getCliente();
    const config = window.SolventaDB.getDemoConfig();
    const esOffline = config.modoOfflineSimulado;

    return `
      <div>
        <div style="text-align:center;padding:var(--e4) 0;">
          <div style="width:64px;height:64px;border-radius:50%;background:var(--primario-suave);color:var(--primario);font-weight:800;font-size:24px;display:grid;place-items:center;margin:0 auto var(--e2);">
            MR
          </div>
          <h2 style="font-size:var(--t-lg);">${cliente.nombre}</h2>
          <p style="color:var(--texto-sec);font-size:var(--t-sm);margin:0;">${cliente.tipoDocumento} ${cliente.documento}</p>
        </div>

        <ul class="lista-movil" style="margin-bottom:var(--e4);">
          <li class="lista-movil-item">
            <div class="icono-bolsa">${window.ICONOS.globo(20)}</div>
            <div class="crece">
              <strong>${tr('idioma')}</strong>
              <span>${state.idioma === 'es' ? 'Español' : 'English'}</span>
            </div>
            <button type="button" class="btn-movil btn-movil-secundario" id="btnSwitchIdioma" style="width:auto;min-height:32px;font-size:11px;padding:0 12px;">
              Cambiar
            </button>
          </li>
          <li class="lista-movil-item">
            <div class="icono-bolsa">${window.ICONOS.wifi(20)}</div>
            <div class="crece">
              <strong>Conexión Móvil</strong>
              <span>${esOffline ? 'Modo sin señal (Offline)' : 'Conexión activa 4G/WiFi'}</span>
            </div>
            <button type="button" class="btn-movil btn-movil-secundario" id="btnToggleConexionCuenta" style="width:auto;min-height:32px;font-size:11px;padding:0 12px;">
              ${esOffline ? 'Conectar' : 'Desconectar'}
            </button>
          </li>
        </ul>

        <button type="button" class="btn-movil btn-movil-secundario" id="btnCerrarSesion" style="color:var(--error);border-color:rgba(220,38,38,0.25);">
          ${window.ICONOS.candado(18)} Bloquear / Cerrar Sesión
        </button>
      </div>
    `;
  }

  // --- Render Maestro ---
  function render() {
    renderCabecera();

    const contenedor = document.getElementById('movilLienzo');
    if (!contenedor) return;

    if (!state.autenticado) {
      if (state.vistaActual === 'loginAlt') {
        contenedor.innerHTML = renderLoginAlternativo();
      } else {
        contenedor.innerHTML = renderBiometria();
      }
    } else {
      if (state.vistaActual === 'billetera') {
        contenedor.innerHTML = renderBilletera();
      } else if (state.vistaActual === 'siniestros') {
        contenedor.innerHTML = renderSiniestros();
      } else if (state.vistaActual === 'cuenta') {
        contenedor.innerHTML = renderCuenta();
      }
    }

    enlazarEventos();
  }

  // --- Enlace de Eventos ---
  function enlazarEventos() {
    // Giro del Carné 3D
    const carne = document.getElementById('carneInteractivo');
    if (carne) {
      carne.addEventListener('click', () => {
        state.carneVolteado = !state.carneVolteado;
        const c = carne.querySelector('.carne-card');
        if (c) c.classList.toggle('volteada', state.carneVolteado);
      });
    }

    // Botón reportar desde billetera
    const btnAccionReportar = document.getElementById('btnAccionReportar');
    if (btnAccionReportar) {
      btnAccionReportar.addEventListener('click', () => {
        state.vistaActual = 'siniestros';
        state.reporte.paso = 1;
        render();
      });
    }

    // Biometría
    const btnSensor = document.getElementById('btnSensorBiometrico');
    if (btnSensor) {
      btnSensor.addEventListener('click', () => {
        btnSensor.classList.add('escaneando');
        const feedback = document.getElementById('sensorFeedback');
        if (feedback) feedback.textContent = tr('sensorExito');
        setTimeout(() => {
          state.autenticado = true;
          window.sessionStorage.setItem('solventa_movil_auth', 'true');
          state.vistaActual = 'billetera';
          render();
        }, 550);
      });
    }

    const btnIrLoginAlt = document.getElementById('btnIrLoginAlt');
    if (btnIrLoginAlt) {
      btnIrLoginAlt.addEventListener('click', () => {
        state.vistaActual = 'loginAlt';
        render();
      });
    }

    const btnVolverBiometria = document.getElementById('btnVolverBiometria');
    if (btnVolverBiometria) {
      btnVolverBiometria.addEventListener('click', () => {
        state.vistaActual = 'biometria';
        render();
      });
    }

    const btnEntrarLoginAlt = document.getElementById('btnEntrarLoginAlt');
    if (btnEntrarLoginAlt) {
      btnEntrarLoginAlt.addEventListener('click', () => {
        state.autenticado = true;
        window.sessionStorage.setItem('solventa_movil_auth', 'true');
        state.vistaActual = 'billetera';
        render();
      });
    }

    // Selección de fotos demo
    document.querySelectorAll('[data-select-foto]').forEach((elem) => {
      elem.addEventListener('click', () => {
        state.reporte.fotoSeleccionada = elem.dataset.selectFoto;
        render();
      });
    });

    // Pasos siniestro
    const btnPasoSiguiente = document.getElementById('btnPasoSiguiente');
    if (btnPasoSiguiente) {
      btnPasoSiguiente.addEventListener('click', () => {
        state.reporte.paso = 2;
        render();
      });
    }

    const btnPasoAtras = document.getElementById('btnPasoAtras');
    if (btnPasoAtras) {
      btnPasoAtras.addEventListener('click', () => {
        state.reporte.paso = 1;
        render();
      });
    }

    const btnEnviarSiniestroFinal = document.getElementById('btnEnviarSiniestroFinal');
    if (btnEnviarSiniestroFinal) {
      btnEnviarSiniestroFinal.addEventListener('click', () => {
        const config = window.SolventaDB.getDemoConfig();
        const esOffline = config.modoOfflineSimulado;

        if (esOffline) {
          const item = window.SolventaDB.encolarSiniestroOffline({
            polizaId: state.reporte.polizaId,
            descripcion: state.reporte.descripcion,
            ubicacion: state.reporte.ubicacion,
          });
          state.reporte.paso = 'offline_queue';
          state.reporte.itemEncoladoId = item.idLocal;
          render();
        } else {
          const nuevo = window.SolventaDB.radicarSiniestro({
            polizaId: state.reporte.polizaId,
            descripcion: state.reporte.descripcion,
            ubicacion: state.reporte.ubicacion,
          });
          state.reporte.siniestroActivoId = nuevo.id;
          state.reporte.paso = 'radicado';
          render();
        }
      });
    }

    const btnVolverBilleteraDesdeCola = document.getElementById('btnVolverBilleteraDesdeCola');
    if (btnVolverBilleteraDesdeCola) {
      btnVolverBilleteraDesdeCola.addEventListener('click', () => {
        state.vistaActual = 'billetera';
        state.reporte.paso = 1;
        render();
      });
    }

    const btnNuevoReporte = document.getElementById('btnNuevoReporte');
    if (btnNuevoReporte) {
      btnNuevoReporte.addEventListener('click', () => {
        state.reporte.paso = 1;
        render();
      });
    }

    // Toggle de conexión rápida desde los pills
    const toggleOnlinePill = document.getElementById('toggleOnlinePill');
    if (toggleOnlinePill) {
      toggleOnlinePill.addEventListener('click', () => {
        window.SolventaDB.setDemoConfig('modoOfflineSimulado', false);
        window.SolventaDB.sincronizarColaOffline();
        render();
      });
    }

    const toggleOfflinePill = document.getElementById('toggleOfflinePill');
    if (toggleOfflinePill) {
      toggleOfflinePill.addEventListener('click', () => {
        window.SolventaDB.setDemoConfig('modoOfflineSimulado', true);
        render();
      });
    }

    const avisoColaSyncClick = document.getElementById('avisoColaSyncClick');
    if (avisoColaSyncClick) {
      avisoColaSyncClick.addEventListener('click', () => {
        window.SolventaDB.setDemoConfig('modoOfflineSimulado', false);
        const rad = window.SolventaDB.sincronizarColaOffline();
        alert(`¡Conexión restaurada! Se radicaron ${rad.length} siniestros pendientes.`);
        render();
      });
    }

    // Cuenta / Perfil
    const btnSwitchIdioma = document.getElementById('btnSwitchIdioma');
    if (btnSwitchIdioma) {
      btnSwitchIdioma.addEventListener('click', () => {
        state.idioma = state.idioma === 'es' ? 'en' : 'es';
        render();
      });
    }

    const btnToggleConexionCuenta = document.getElementById('btnToggleConexionCuenta');
    if (btnToggleConexionCuenta) {
      btnToggleConexionCuenta.addEventListener('click', () => {
        const config = window.SolventaDB.getDemoConfig();
        const nuevo = !config.modoOfflineSimulado;
        window.SolventaDB.setDemoConfig('modoOfflineSimulado', nuevo);
        if (!nuevo) {
          window.SolventaDB.sincronizarColaOffline();
        }
        render();
      });
    }

    const btnCerrarSesion = document.getElementById('btnCerrarSesion');
    if (btnCerrarSesion) {
      btnCerrarSesion.addEventListener('click', () => {
        state.autenticado = false;
        window.sessionStorage.removeItem('solventa_movil_auth');
        state.vistaActual = 'biometria';
        render();
      });
    }
  }

  // --- Inicio ---
  function iniciar() {
    // Tabbar
    document.querySelectorAll('.tab-item-movil').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.vistaActual = btn.dataset.vista;
        render();
      });
    });

    // Idioma
    const selIdioma = document.getElementById('selIdiomaMovil');
    if (selIdioma) {
      selIdioma.addEventListener('change', (e) => {
        state.idioma = e.target.value;
        render();
      });
    }

    // Región
    const selRegion = document.getElementById('selRegionMovil');
    if (selRegion) {
      selRegion.addEventListener('change', (e) => {
        state.region = e.target.value;
        render();
      });
    }

    // Tema
    const btnTema = document.getElementById('btnTemaMovil');
    if (btnTema) {
      btnTema.addEventListener('click', () => {
        state.tema = state.tema === 'oscuro' ? 'claro' : 'oscuro';
        render();
      });
    }

    // Clic en la barra de estado para simular pérdida de red o conexión
    const barraEstadoIconos = document.querySelector('.barra-estado-iconos');
    if (barraEstadoIconos) {
      barraEstadoIconos.addEventListener('click', () => {
        const config = window.SolventaDB.getDemoConfig();
        const nuevo = !config.modoOfflineSimulado;
        window.SolventaDB.setDemoConfig('modoOfflineSimulado', nuevo);
        if (!nuevo) {
          window.SolventaDB.sincronizarColaOffline();
        }
        render();
      });
    }

    // Suscripción a cambios de base de datos
    window.SolventaDB.subscribe(() => {
      render();
    });

    render();
  }

  window.addEventListener('DOMContentLoaded', iniciar);
})();

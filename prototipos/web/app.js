/* ============================================================================
   Solventa · Prototipo Web Ejecutable (Validación de Interfaz con Usuario Final)
   Flujo interactivo con autenticación simulada, cotización personalizada en vivo,
   emisión digital amigable y gestión de pólizas sin tecnicismos.
   ========================================================================= */

(function () {
  const urlParams = new URLSearchParams(window.location.search);

  const state = {
    // Autenticación simulada: inicia en false a menos que ya se haya iniciado sesión en la pestaña
    sesionIniciada: window.sessionStorage.getItem('solventa_web_auth') === 'true',
    pestana: urlParams.get('pestana') || 'cotizador',
    paso: Math.min(4, Math.max(1, parseInt(urlParams.get('paso') || '1', 10))),
    idioma: ['es', 'en'].includes(urlParams.get('idioma')) ? urlParams.get('idioma') : 'es',
    region: ['CO', 'MX', 'CL', 'PE'].includes(urlParams.get('region')) ? urlParams.get('region') : 'CO',
    tema: urlParams.get('tema') === 'oscuro' ? 'oscuro' : 'claro',

    // Formulario de Cliente y Crédito (Paso 1)
    cliente: {
      documento: '1.032.456.789',
      tipoDocumento: 'CC',
      nombre: 'María Fernanda Ruiz',
      edad: 35,
      telefono: '+57 310 555 4417',
      correo: 'maria.ruiz@correo.co',
      entidad: 'Banco Aliado S.A.',
      monto: 250000000,
      plazo: 180,
    },

    // Consentimiento (Paso 2)
    consentimiento: {
      otorgado: true,
      otpEnviado: false,
      otpIngresado: '417902',
      otpValido: true,
    },

    // Emisión (Paso 4)
    emision: {
      metodoPago: 'tarjeta',
      referenciaSegura: 'REF-SEG-2026-99120',
      polizaEmitida: null,
      rechazoManualSolicitado: false,
    },

    // Gestión de Pólizas
    gestion: {
      filtroTexto: '',
      filtroEstado: 'todos',
      polizaSeleccionadaId: 'POL-2026-004182',
      tabDetalle: 'coberturas',
    },

    // Canal Banco Aliado
    socio: {
      ofertaDisponible: true,
      ofertaAceptada: false,
    },
  };

  // Inicializar monto base según región
  state.cliente.monto = window.REGIONES[state.region].montoBase;

  const tr = (k) => window.t(k, state.idioma);
  const fmtMoneda = (val) => window.formatoDinero(val, state.region);
  const fmtFecha = (iso) => window.formatoFecha(iso, state.region);

  // --- Motor de Cálculo de Prima Actuarial en Vivo ---
  function calcularCotizacion() {
    const reg = window.REGIONES[state.region] || window.REGIONES.CO;
    const monto = parseFloat(state.cliente.monto) || reg.montoBase;
    const edad = parseInt(state.cliente.edad, 10) || 35;
    const plazo = parseInt(state.cliente.plazo, 10) || 180;

    let factorEdad = 1.0;
    if (edad <= 30) factorEdad = 0.92;
    else if (edad <= 40) factorEdad = 1.0;
    else if (edad <= 50) factorEdad = 1.18;
    else factorEdad = 1.42;

    let factorPlazo = 1.0;
    if (plazo <= 120) factorPlazo = 0.95;
    else if (plazo <= 240) factorPlazo = 1.0;
    else factorPlazo = 1.08;

    const primaNormal = Math.round(monto * reg.factorTasa * factorEdad * factorPlazo);
    const demoConfig = window.SolventaDB.getDemoConfig();
    const esDegradado = demoConfig.modoDegradadoForzado;
    const primaFinal = esDegradado ? Math.round(primaNormal * 1.04) : primaNormal;
    const primaMercado = Math.round(primaNormal * 1.22);
    const ahorro = primaMercado - primaFinal;

    const desglose = {
      tarifaBase: Math.round(primaFinal * 0.62),
      ajusteRiesgo: Math.round(primaFinal * 0.18),
      ajusteEdad: Math.round(primaFinal * 0.11),
      impuestos: Math.round(primaFinal * 0.09),
    };

    return {
      monto,
      edad,
      plazo,
      primaNormal,
      primaFinal,
      primaMercado,
      ahorro,
      esDegradado,
      desglose,
    };
  }

  // --- Renderizado de Cabecera ---
  function renderCabecera() {
    document.documentElement.lang = state.idioma;
    document.documentElement.dataset.tema = state.tema;

    const cabecera = document.querySelector('.cabecera-web');
    if (cabecera) {
      cabecera.style.display = state.sesionIniciada ? 'flex' : 'none';
    }
    document.body.classList.toggle('modo-login', !state.sesionIniciada);

    const selIdioma = document.getElementById('selIdioma');
    const selRegion = document.getElementById('selRegion');
    const btnTema = document.getElementById('btnTema');
    const navTabs = document.querySelector('.nav-tabs');
    const perfilUsuario = document.getElementById('perfilUsuario');

    if (selIdioma) selIdioma.value = state.idioma;
    if (selRegion) {
      selRegion.innerHTML = Object.entries(window.REGIONES)
        .map(([cod, r]) => `<option value="${cod}" ${cod === state.region ? 'selected' : ''}>${r.etiqueta} (${r.moneda})</option>`)
        .join('');
    }
    if (btnTema) {
      btnTema.innerHTML = state.tema === 'oscuro' ? window.ICONOS.sol(18) : window.ICONOS.luna(18);
      btnTema.setAttribute('aria-label', state.tema === 'oscuro' ? tr('temaClaro') : tr('temaOscuro'));
    }

    if (navTabs) {
      navTabs.style.display = state.sesionIniciada ? 'flex' : 'none';
      document.querySelectorAll('.tab-btn').forEach((btn) => {
        const p = btn.dataset.pestana;
        btn.classList.toggle('activo', p === state.pestana);
      });
    }

    if (perfilUsuario) {
      perfilUsuario.style.display = state.sesionIniciada ? 'flex' : 'none';
    }
  }

  // --- Vista W1: Autenticación Simulada del Asesor (Fiel al Mockup) ---
  function renderLogin() {
    return `
      <div class="login-split">
        <div class="login-panel-marca">
          <div class="login-marca-contenido">
            <h1 class="login-marca-titulo">${tr('loginTitulo')}</h1>
            <p class="login-marca-subtitulo">${tr('loginLema')}</p>
          </div>
        </div>
        <div class="login-panel-form">
          <div class="login-form-box">
            <h2 class="login-form-titulo">${tr('loginFormTitulo')}</h2>
            <form id="formLoginWeb" class="login-formulario-body" onsubmit="return false;">
              <div class="login-campo">
                <label for="loginUser">${tr('usuarioCorp')}</label>
                <input id="loginUser" type="email" value="asesor@solventa.co" required autocomplete="username">
              </div>
              <div class="login-campo">
                <label for="loginPass">${tr('clave')}</label>
                <input id="loginPass" type="password" value="••••••••" required autocomplete="current-password">
              </div>
              <div class="login-olvide-wrap">
                <a href="#" id="linkOlvideClave" class="login-olvide-link">${tr('olvideClave')}</a>
              </div>
              <button type="submit" class="login-btn-entrar" id="btnIniciarSesionWeb">
                ${window.ICONOS.llave(16)}
                <span>${tr('btnEntrar')}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    `;
  }

  // --- Renderizado de Stepper del Cotizador ---
  function renderStepper() {
    const contenedor = document.getElementById('stepperContainer');
    if (!contenedor) return;

    const pasos = [
      { id: 1, clave: 'paso1' },
      { id: 2, clave: 'paso2' },
      { id: 3, clave: 'paso3' },
      { id: 4, clave: 'paso4' },
    ];

    contenedor.innerHTML = pasos
      .map((p, i) => {
        const activo = state.paso === p.id;
        const hecho = state.paso > p.id;
        const clase = activo ? 'activo' : hecho ? 'hecho' : '';
        const numero = hecho ? '✓' : p.id;
        return `
          <div class="paso-item ${clase}" data-ir-paso="${p.id}">
            <div class="paso-numero">${numero}</div>
            <span>${tr(p.clave)}</span>
          </div>
          ${i < pasos.length - 1 ? '<div class="paso-divisor"></div>' : ''}
        `;
      })
      .join('');
  }

  // --- Vista Paso 1: Identificación ---
  function renderPaso1() {
    return `
      <div class="vista-header">
        <h2>${tr('p1Titulo')}</h2>
        <p>${tr('p1Subtitulo')}</p>
      </div>

      <div class="pila">
        <section class="panel">
          <header>
            <h4>${window.ICONOS.usuario(18)} ${tr('seccionCliente')}</h4>
            <span class="chip ok">Cliente Identificado</span>
          </header>
          <div class="contenido">
            <div class="dos-iguales">
              <div class="campo">
                <label for="inpDoc">${tr('documento')}</label>
                <input id="inpDoc" type="text" value="${state.cliente.documento}">
              </div>
              <div class="campo">
                <label for="inpNom">${tr('nombre')}</label>
                <input id="inpNom" type="text" value="${state.cliente.nombre}">
              </div>
              <div class="campo">
                <label for="inpEdad">${tr('edad')}</label>
                <input id="inpEdad" type="number" min="18" max="75" value="${state.cliente.edad}">
              </div>
              <div class="campo">
                <label for="inpTel">${tr('telefono')}</label>
                <input id="inpTel" type="text" value="${state.cliente.telefono}">
              </div>
            </div>
          </div>
        </section>

        <section class="panel">
          <header>
            <h4>${window.ICONOS.tarjeta(18)} ${tr('seccionCredito')}</h4>
            <span class="chip neutro">Crédito Hipotecario</span>
          </header>
          <div class="contenido">
            <div class="tres-columnas">
              <div class="campo">
                <label for="inpEnt">${tr('entidad')}</label>
                <input id="inpEnt" type="text" value="${state.cliente.entidad}">
              </div>
              <div class="campo">
                <label for="inpMonto">${tr('monto')} (${window.REGIONES[state.region].moneda})</label>
                <input id="inpMonto" type="number" step="${window.REGIONES[state.region].pasoMonto}" value="${state.cliente.monto}">
                <small style="color:var(--texto-sec);margin-top:2px;">${fmtMoneda(state.cliente.monto)}</small>
              </div>
              <div class="campo">
                <label for="inpPlazo">${tr('plazo')}</label>
                <input id="inpPlazo" type="number" min="36" max="360" step="12" value="${state.cliente.plazo}">
              </div>
            </div>
          </div>
        </section>

        <div style="display:flex;justify-content:flex-end;margin-top:var(--e3)">
          <button type="button" class="btn btn-primario" id="btnIrPaso2">
            ${tr('continuarConsentimiento')} &rarr;
          </button>
        </div>
      </div>
    `;
  }

  // --- Vista Paso 2: Consentimiento ---
  function renderPaso2() {
    return `
      <div class="vista-header">
        <h2>${tr('p2Titulo')}</h2>
        <p>${tr('p2Subtitulo')}</p>
      </div>

      <div class="dos-columnas">
        <div class="pila">
          <section class="panel">
            <header>
              <h4>${tr('datosConsultados')}</h4>
              <span class="chip neutro">3 fuentes</span>
            </header>
            <div class="contenido pila">
              <div style="display:flex;gap:var(--e3);align-items:flex-start">
                <span style="color:var(--primario);flex:none">${window.ICONOS.enchufe(22)}</span>
                <div>
                  <strong>${tr('fuenteOF')}</strong>
                  <p style="margin:2px 0 0;font-size:var(--t-xs);color:var(--texto-sec);">${tr('detalleOF')}</p>
                </div>
              </div>
              <div style="display:flex;gap:var(--e3);align-items:flex-start">
                <span style="color:var(--acento);flex:none">${window.ICONOS.globo(22)}</span>
                <div>
                  <strong>${tr('fuenteOD')}</strong>
                  <p style="margin:2px 0 0;font-size:var(--t-xs);color:var(--texto-sec);">${tr('detalleOD')}</p>
                </div>
              </div>
              <div style="display:flex;gap:var(--e3);align-items:flex-start">
                <span style="color:var(--ok);flex:none">${window.ICONOS.candado(22)}</span>
                <div>
                  <strong>${tr('fuenteKYC')}</strong>
                  <p style="margin:2px 0 0;font-size:var(--t-xs);color:var(--texto-sec);">${tr('detalleKYC')}</p>
                </div>
              </div>
            </div>
          </section>

          <section class="panel">
            <header>
              <h4>${tr('autorizaCliente')}</h4>
              <span class="chip ${state.consentimiento.otpValido ? 'ok' : 'aviso'}">
                ${state.consentimiento.otpValido ? tr('autorizadoOk') : tr('esperandoCliente')}
              </span>
            </header>
            <div class="contenido">
              <p style="font-size:var(--t-sm);margin:0 0 var(--e3)">${tr('autorizaTexto')}</p>
              
              <label style="display:flex;align-items:center;gap:var(--e2);cursor:pointer;margin-bottom:var(--e4)">
                <input type="checkbox" id="chkConsentimiento" ${state.consentimiento.otorgado ? 'checked' : ''}>
                <span style="font-size:var(--t-sm);font-weight:600;">${tr('marcarConsentimiento')}</span>
              </label>

              <div class="aviso info" style="margin-bottom:var(--e3)">
                ${window.ICONOS.movil(22)}
                <div style="flex:1">
                  <strong>${tr('verificacionOtp')}</strong>
                  <span>${tr('otpEnviado')}: <code>${state.cliente.telefono}</code></span>
                </div>
                <button type="button" class="btn btn-secundario" id="btnSimularOtp" style="min-height:32px;font-size:11px;">
                  ${tr('simularOtp')}
                </button>
              </div>

              <div style="display:flex;gap:var(--e3);align-items:center;">
                <div class="campo" style="margin:0;max-width:180px;">
                  <input id="inpOtp" type="text" placeholder="123456" maxlength="6" value="${state.consentimiento.otpIngresado}">
                </div>
                <span style="font-size:var(--t-xs);color:var(--ok);font-weight:600;">
                  ${state.consentimiento.otpValido ? '✓ Código SMS verificado exitosamente' : ''}
                </span>
              </div>
            </div>
          </section>

          <p style="font-size:var(--t-xs);color:var(--texto-sec);">${tr('baseLegal')}</p>
        </div>

        <aside class="pila">
          <section class="panel">
            <header>
              <h4>Resumen Solicitante</h4>
            </header>
            <div class="contenido pila">
              <div>
                <span style="font-size:var(--t-xs);color:var(--texto-sec);">Titular:</span>
                <strong style="display:block;">${state.cliente.nombre}</strong>
                <span style="font-size:var(--t-xs);">${state.cliente.tipoDocumento} ${state.cliente.documento}</span>
              </div>
              <div>
                <span style="font-size:var(--t-xs);color:var(--texto-sec);">Monto Solicitado:</span>
                <strong style="display:block;font-size:var(--t-md);color:var(--primario);">${fmtMoneda(state.cliente.monto)}</strong>
                <span style="font-size:var(--t-xs);">${state.cliente.plazo} meses · ${state.cliente.entidad}</span>
              </div>
            </div>
          </section>

          <button type="button" class="btn btn-primario btn-ancho" id="btnIrPaso3">
            ${window.ICONOS.rayo(18)} ${tr('cotizarAhora')} &rarr;
          </button>
          
          <button type="button" class="btn btn-secundario btn-ancho" id="btnVolverPaso1">
            &larr; Volver a datos
          </button>
        </aside>
      </div>
    `;
  }

  // --- Vista Paso 3: Cotización Viva & Desglose ---
  function renderPaso3() {
    const c = calcularCotizacion();

    return `
      <div class="vista-header">
        <h2>${tr('p3Titulo')}</h2>
        <p>${tr('p3Subtitulo')}</p>
      </div>

      ${
        c.esDegradado
          ? `
        <div class="aviso atencion">
          ${window.ICONOS.alerta(24)}
          <div style="flex:1">
            <strong>${tr('perfilParcialChip')}</strong>
            <p style="margin:4px 0;">${tr('avisoDegradado')}</p>
            <span style="font-size:var(--t-xs);color:var(--aviso);">${tr('antiguedadPerfil')}</span>
          </div>
          <button type="button" class="btn btn-secundario" id="btnReintentarOF" style="min-height:34px;font-size:12px;">
            ${window.ICONOS.refrescar(14)} ${tr('reintentarOpenFinance')}
          </button>
        </div>`
          : ''
      }

      <div class="dos-columnas">
        <div class="pila">
          <section class="panel">
            <header>
              <h4>${tr('primaMensual')}</h4>
              <span class="chip ${c.esDegradado ? 'aviso' : 'ok'}">
                ${c.esDegradado ? tr('perfilParcialChip') : tr('perfilCompletoChip')}
              </span>
            </header>
            <div class="contenido">
              <div class="hero-precio">
                <span class="valor">${fmtMoneda(c.primaFinal)}</span>
                <span class="unidad">/ ${tr('primaMensual').toLowerCase()}</span>
                <span class="comparativo">
                  <s>${fmtMoneda(c.primaMercado)}</s> ${tr('ahorro')}: <strong>${fmtMoneda(c.ahorro)}</strong>
                </span>
              </div>

              <p style="font-size:var(--t-xs);color:var(--texto-sec);margin:0 0 var(--e3);">
                ${window.ICONOS.reloj(14)} ${c.esDegradado ? tr('antiguedadPerfil') : `${tr('calculadaEn')} · ${tr('origenCompleto')}`}
              </p>

              <h5 style="margin:var(--e4) 0 var(--e2);font-size:var(--t-sm);">${tr('desgloseTitulo')}</h5>
              <ul class="desglose-lista">
                <li>
                  <div class="desglose-fila">
                    <span>${tr('tarifaBase')} (62%)</span>
                    <strong>${fmtMoneda(c.desglose.tarifaBase)}</strong>
                  </div>
                  <div class="barra-progreso"><span style="width: 62%;"></span></div>
                </li>
                <li>
                  <div class="desglose-fila">
                    <span>${tr('ajusteRiesgo')} (18%)</span>
                    <strong>${fmtMoneda(c.desglose.ajusteRiesgo)}</strong>
                  </div>
                  <div class="barra-progreso"><span style="width: 18%;"></span></div>
                </li>
                <li>
                  <div class="desglose-fila">
                    <span>${tr('ajusteEdad')} (11%)</span>
                    <strong>${fmtMoneda(c.desglose.ajusteEdad)}</strong>
                  </div>
                  <div class="barra-progreso"><span style="width: 11%;"></span></div>
                </li>
                <li>
                  <div class="desglose-fila">
                    <span>${tr('impuestos')} (9%)</span>
                    <strong>${fmtMoneda(c.desglose.impuestos)}</strong>
                  </div>
                  <div class="barra-progreso"><span style="width: 9%;"></span></div>
                </li>
              </ul>
            </div>
          </section>
        </div>

        <aside class="pila">
          <section class="panel">
            <header>
              <h4>${tr('resumenRiesgo')}</h4>
            </header>
            <div class="contenido pila">
              <div>
                <span style="font-size:var(--t-xs);color:var(--texto-sec);">${tr('nivelRiesgo')}</span>
                <p style="margin:2px 0 0;font-weight:700;color:var(--ok);">${tr('nivelBajo')}</p>
              </div>
              <div>
                <span style="font-size:var(--t-xs);color:var(--texto-sec);">${tr('factoresPrecio')}</span>
                <ul class="lista-check" style="margin-top:var(--e2);">
                  <li><span class="si">${window.ICONOS.check(16)}</span> ${tr('factor1')}</li>
                  <li><span class="si">${window.ICONOS.check(16)}</span> ${tr('factor2')}</li>
                  <li><span class="si">${window.ICONOS.check(16)}</span> ${tr('factor3')}</li>
                </ul>
              </div>
              <div>
                <span style="font-size:var(--t-xs);color:var(--texto-sec);">${tr('coberturasIncluidas')}</span>
                <ul class="lista-check" style="margin-top:var(--e2);">
                  <li><span class="si">${window.ICONOS.escudo(16)}</span> ${tr('cob1')}</li>
                  <li><span class="si">${window.ICONOS.escudo(16)}</span> ${tr('cob2')}</li>
                  <li><span class="si">${window.ICONOS.escudo(16)}</span> ${tr('cob3')}</li>
                </ul>
              </div>
            </div>
          </section>

          <p style="font-size:var(--t-xs);color:var(--texto-sec);">${tr('vigenciaOferta')}</p>

          <button type="button" class="btn btn-primario btn-ancho" id="btnIrPaso4">
            ${window.ICONOS.escudo(18)} ${tr('irAEmision')} &rarr;
          </button>
          
          <button type="button" class="btn btn-secundario btn-ancho" id="btnVolverPaso2">
            &larr; Volver al consentimiento
          </button>
        </aside>
      </div>
    `;
  }

  // --- Vista Paso 4: Emisión, Pago & Confirmación ---
  function renderPaso4() {
    const c = calcularCotizacion();
    const demoConfig = window.SolventaDB.getDemoConfig();
    const esRechazo = demoConfig.modoRechazoForzado;

    return `
      <div class="vista-header">
        <h2>${tr('p4Titulo')}</h2>
        <p>${tr('p4Subtitulo')}</p>
      </div>

      ${
        state.emision.polizaEmitida
          ? `
        <div class="aviso exito" style="padding:var(--e5);flex-direction:column;align-items:flex-start;">
          <div style="display:flex;gap:var(--e3);align-items:center;">
            <span style="color:var(--ok);">${window.ICONOS.check(32)}</span>
            <div>
              <h3 style="color:var(--ok);font-size:var(--t-lg);">${tr('polizaEmitidaExito')}</h3>
              <p style="margin:4px 0 0;font-size:var(--t-base);">
                ${tr('polizaNumGenerada')}: <strong>${state.emision.polizaEmitida.id}</strong>
              </p>
            </div>
          </div>
          <div style="display:flex;gap:var(--e3);margin-top:var(--e4);">
            <button type="button" class="btn btn-primario" id="btnVerEnGestion">
              ${window.ICONOS.buscar(18)} ${tr('verEnGestion')}
            </button>
            <button type="button" class="btn btn-secundario" id="btnNuevaCotizacion">
              + Nueva Cotización
            </button>
          </div>
        </div>
      `
          : ''
      }

      ${
        esRechazo && !state.emision.polizaEmitida
          ? `
        <div class="aviso error" style="flex-direction:column;align-items:flex-start;padding:var(--e4);">
          <div style="display:flex;gap:var(--e3);align-items:center;">
            ${window.ICONOS.equis(28)}
            <div>
              <strong>${tr('rechazoTitulo')}</strong>
              <p style="margin:4px 0 0;">${tr('rechazoMotivo')}</p>
            </div>
          </div>
          ${
            state.emision.rechazoManualSolicitado
              ? `<div class="chip ok" style="margin-top:var(--e3);">${tr('solicitudEnviada')}</div>`
              : `<button type="button" class="btn btn-secundario" id="btnPedirRevision" style="margin-top:var(--e3);">
                  ${tr('solicitarRevision')}
                 </button>`
          }
        </div>
      `
          : ''
      }

      <div class="dos-columnas">
        <div class="pila">
          <section class="panel">
            <header>
              <h4>${tr('pasosEmision')}</h4>
              <span class="chip ${state.emision.polizaEmitida ? 'ok' : 'neutro'}">
                ${state.emision.polizaEmitida ? '4 / 4' : '3 / 4'}
              </span>
            </header>
            <div class="contenido">
              <ol class="linea-tiempo">
                <li class="hecho">
                  <strong>${tr('pasoCobro')}</strong>
                  <span class="cuando">${state.emision.polizaEmitida ? tr('completado') : tr('pendiente')}</span>
                </li>
                <li class="hecho">
                  <strong>${tr('pasoFirma')}</strong>
                  <span class="cuando">${tr('completado')} (Firma electrónica)</span>
                </li>
                <li class="${state.emision.polizaEmitida ? 'hecho' : 'actual'}">
                  <strong>${tr('pasoPoliza')}</strong>
                  <span class="cuando">${state.emision.polizaEmitida ? tr('completado') : 'Lista para formalizar'}</span>
                </li>
                <li class="${state.emision.polizaEmitida ? 'hecho' : ''}">
                  <strong>${tr('pasoEnvio')}</strong>
                  <span class="cuando">${state.emision.polizaEmitida ? 'Certificado enviado al correo y billetera' : tr('pendiente')}</span>
                </li>
              </ol>
            </div>
          </section>

          <div class="aviso info">
            ${window.ICONOS.candado(24)}
            <div>
              <strong>${tr('referenciaPago')}</strong>
              <p style="margin:2px 0 4px;font-family:monospace;font-size:13px;font-weight:700;">${state.emision.referenciaSegura}</p>
              <span style="font-size:var(--t-xs);color:var(--texto-sec);">${tr('seguridadAviso')}</span>
            </div>
          </div>
        </div>

        <aside class="pila">
          <section class="panel">
            <header>
              <h4>${tr('resumenCompra')}</h4>
            </header>
            <div class="contenido pila">
              <div style="display:flex;justify-content:space-between;font-size:var(--t-sm);">
                <span style="color:var(--texto-sec);">${tr('productoSeguro')}:</span>
                <strong>${tr('vidaHipotecario')}</strong>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:var(--t-sm);">
                <span style="color:var(--texto-sec);">${tr('sumaAsegurada')}:</span>
                <strong>${fmtMoneda(c.monto)}</strong>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:var(--t-sm);">
                <span style="color:var(--texto-sec);">${tr('metodoPago')}:</span>
                <span>${tr('tarjeta')}</span>
              </div>
              <div style="border-top:1px solid var(--borde);padding-top:var(--e3);display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:700;">${tr('totalPagar')}:</span>
                <span style="font-size:var(--t-xl);font-weight:800;color:var(--primario);">${fmtMoneda(c.primaFinal)}</span>
              </div>
            </div>
          </section>

          ${
            !state.emision.polizaEmitida && !esRechazo
              ? `
            <button type="button" class="btn btn-primario btn-ancho" id="btnEjecutarPago">
              ${window.ICONOS.tarjeta(18)} ${tr('pagarYEmitir')}
            </button>
          `
              : ''
          }

          <button type="button" class="btn btn-secundario btn-ancho" id="btnVolverPaso3">
            &larr; Volver a cotización
          </button>
        </aside>
      </div>
    `;
  }

  // --- Vista Gestión de Pólizas (Búsqueda y Detalle) ---
  function renderGestion() {
    const polizas = window.SolventaDB.getPolizas();
    const filtro = state.gestion.filtroTexto.toLowerCase().trim();
    const filtroEst = state.gestion.filtroEstado;

    const polizasFiltradas = polizas.filter((p) => {
      const coincideTexto =
        !filtro ||
        p.id.toLowerCase().includes(filtro) ||
        p.clienteNombre.toLowerCase().includes(filtro) ||
        p.clienteDocumento.includes(filtro);
      const coincideEstado = filtroEst === 'todos' || p.estado === filtroEst;
      return coincideTexto && coincideEstado;
    });

    const polizaActual =
      polizas.find((p) => p.id === state.gestion.polizaSeleccionadaId) || polizasFiltradas[0] || polizas[0];

    const siniestrosDePoliza = polizaActual ? window.SolventaDB.getSiniestrosPorPoliza(polizaActual.id) : [];

    return `
      <div class="vista-header">
        <h2>${tr('gTitulo')}</h2>
        <p>${tr('gSubtitulo')}</p>
      </div>

      <div class="dos-columnas">
        <div class="pila">
          <section class="panel">
            <header>
              <h4>Lista de Pólizas</h4>
              <span class="chip neutro">${polizasFiltradas.length} encontradas</span>
            </header>
            <div class="contenido">
              <div style="display:flex;gap:var(--e3);margin-bottom:var(--e4);flex-wrap:wrap;">
                <div style="flex:1;min-width:240px;" class="campo">
                  <input id="inpBuscarGestion" type="text" placeholder="${tr('buscarPlaceholder')}" value="${state.gestion.filtroTexto}">
                </div>
                <div style="width:160px;" class="campo">
                  <select id="selFiltroEstado">
                    <option value="todos" ${state.gestion.filtroEstado === 'todos' ? 'selected' : ''}>${tr('filtroTodos')}</option>
                    <option value="vigente" ${state.gestion.filtroEstado === 'vigente' ? 'selected' : ''}>${tr('vigente')}</option>
                    <option value="pendiente" ${state.gestion.filtroEstado === 'pendiente' ? 'selected' : ''}>${tr('pendienteEstado')}</option>
                    <option value="rechazada" ${state.gestion.filtroEstado === 'rechazada' ? 'selected' : ''}>${tr('rechazada')}</option>
                  </select>
                </div>
              </div>

              <div class="tabla-envoltura">
                <table class="tabla">
                  <thead>
                    <tr>
                      <th>${tr('colPoliza')}</th>
                      <th>${tr('colCliente')}</th>
                      <th>${tr('colRamo')}</th>
                      <th>${tr('colPrima')}</th>
                      <th>${tr('colEstado')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${
                      polizasFiltradas.length === 0
                        ? `<tr><td colspan="5" style="text-align:center;color:var(--texto-sec);">No se encontraron pólizas con los filtros seleccionados.</td></tr>`
                        : polizasFiltradas
                            .map((p) => {
                              const sel = polizaActual && polizaActual.id === p.id ? 'seleccionada' : '';
                              const badgeClase = p.estado === 'vigente' ? 'ok' : p.estado === 'pendiente' ? 'aviso' : 'error';
                              return `
                                <tr class="${sel}" data-seleccionar-poliza="${p.id}">
                                  <td><strong>${p.id}</strong></td>
                                  <td>${p.clienteNombre}<br><span style="font-size:11px;color:var(--texto-sec);">${p.clienteDocumento}</span></td>
                                  <td>${p.ramoNombre}</td>
                                  <td>${fmtMoneda(p.primaMensual)}</td>
                                  <td><span class="chip ${badgeClase}">${p.estado}</span></td>
                                </tr>
                              `;
                            })
                            .join('')
                    }
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>

        <aside class="pila">
          ${
            polizaActual
              ? `
            <section class="panel">
              <header>
                <h4>${polizaActual.id}</h4>
                <span class="chip ${polizaActual.estado === 'vigente' ? 'ok' : 'aviso'}">${polizaActual.estado}</span>
              </header>
              <div class="contenido pila">
                <div style="display:flex;gap:var(--e2);border-bottom:1px solid var(--borde);padding-bottom:var(--e2);">
                  <button type="button" class="btn btn-secundario ${state.gestion.tabDetalle === 'coberturas' ? 'btn-primario' : ''}" id="tabDetCoberturas" style="min-height:32px;font-size:12px;">
                    ${tr('tabCoberturas')}
                  </button>
                  <button type="button" class="btn btn-secundario ${state.gestion.tabDetalle === 'siniestros' ? 'btn-primario' : ''}" id="tabDetSiniestros" style="min-height:32px;font-size:12px;">
                    ${tr('tabSiniestros')} (${siniestrosDePoliza.length})
                  </button>
                </div>

                ${
                  state.gestion.tabDetalle === 'coberturas'
                    ? `
                  <div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:var(--e2);font-size:var(--t-sm);">
                      <span style="color:var(--texto-sec);">${tr('sumaAsegurada')}:</span>
                      <strong>${fmtMoneda(polizaActual.montoAsegurado)}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:var(--e2);font-size:var(--t-sm);">
                      <span style="color:var(--texto-sec);">${tr('primaMensual')}:</span>
                      <strong>${fmtMoneda(polizaActual.primaMensual)}</strong>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:var(--e2);font-size:var(--t-sm);">
                      <span style="color:var(--texto-sec);">Vigencia:</span>
                      <span>${fmtFecha(polizaActual.fechaInicio).split(',')[0]} - ${fmtFecha(polizaActual.fechaVigencia).split(',')[0]}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:var(--t-sm);">
                      <span style="color:var(--texto-sec);">Socio originador:</span>
                      <span>${polizaActual.socio}</span>
                    </div>

                    <h5 style="margin:var(--e4) 0 var(--e2);font-size:var(--t-sm);">Amparos Contratados:</h5>
                    <ul class="lista-check">
                      ${(polizaActual.coberturas || [])
                        .map(
                          (c) =>
                            `<li><span class="si">${window.ICONOS.check(16)}</span> ${c.nombre} ${c.porcentaje ? `(${c.porcentaje}%)` : ''}</li>`
                        )
                        .join('')}
                    </ul>
                  </div>
                `
                    : `
                  <div>
                    ${
                      siniestrosDePoliza.length === 0
                        ? `<p style="color:var(--texto-sec);font-size:var(--t-sm);">${tr('sinSiniestros')}</p>`
                        : siniestrosDePoliza
                            .map((s) => {
                              const badgeColor = s.estado === 'resuelto' ? 'ok' : 'aviso';
                              return `
                            <div style="padding:var(--e3);background:var(--superficie-alt);border-radius:var(--r-sm);border:1px solid var(--borde);margin-bottom:var(--e3);">
                              <div style="display:flex;justify-content:space-between;align-items:center;">
                                <strong>${s.id}</strong>
                                <span class="chip ${badgeColor}">${s.estado}</span>
                              </div>
                              <p style="margin:4px 0;font-size:var(--t-xs);">${s.descripcion}</p>
                              <span style="font-size:11px;color:var(--texto-sec);">${fmtFecha(s.fechaReporte)} · ${s.ubicacion}</span>
                            </div>
                          `;
                            })
                            .join('')
                    }
                  </div>
                `
                }
              </div>
            </section>
          `
              : ''
          }
        </aside>
      </div>
    `;
  }

  // --- Vista Canal Banco Aliado (Experiencia de Usuario del Banco) ---
  function renderSocios() {
    const c = calcularCotizacion();

    return `
      <div class="vista-header">
        <h2>${tr('sTitulo')}</h2>
        <p>${tr('sSubtitulo')}</p>
      </div>

      <div class="dos-columnas">
        <div class="pila">
          <section class="panel">
            <header>
              <h4>${window.ICONOS.monitor(18)} ${tr('simulacionBanco')}</h4>
              <span class="chip ok">Banco Aliado · Banca en Línea</span>
            </header>
            <div class="contenido">
              <p style="color:var(--texto-sec);font-size:var(--t-sm);margin:0 0 var(--e4);">${tr('bancoTexto')}</p>

              <!-- Resumen del crédito en el banco -->
              <div style="background:var(--superficie-alt);border:1px solid var(--borde);border-radius:var(--r-md);padding:var(--e4);margin-bottom:var(--e4);">
                <h5 style="margin:0 0 var(--e3);font-size:var(--t-sm);text-transform:uppercase;color:var(--texto-sec);">Condiciones del Crédito Aprobado</h5>
                <div class="tres-columnas">
                  <div>
                    <span style="font-size:11px;color:var(--texto-sec);">${tr('creditoMonto')}:</span>
                    <strong style="display:block;font-size:var(--t-md);color:var(--primario);">${fmtMoneda(state.cliente.monto)}</strong>
                  </div>
                  <div>
                    <span style="font-size:11px;color:var(--texto-sec);">${tr('plazo')}:</span>
                    <strong style="display:block;font-size:var(--t-md);">${state.cliente.plazo} meses</strong>
                  </div>
                  <div>
                    <span style="font-size:11px;color:var(--texto-sec);">${tr('cuotaCredito')}:</span>
                    <strong style="display:block;font-size:var(--t-md);">${fmtMoneda(state.cliente.monto * 0.0096)}</strong>
                  </div>
                </div>
              </div>

              <!-- Oferta del seguro Solventa embebida -->
              ${
                state.socio.ofertaDisponible
                  ? `
                <div style="border:2px solid var(--primario);border-radius:var(--r-md);padding:var(--e4);background:var(--primario-suave);">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--e2);">
                    <h4 style="color:var(--primario);margin:0;display:flex;align-items:center;gap:6px;">
                      ${window.ICONOS.escudo(20)} Seguro de Vida Hipotecario Solventa
                    </h4>
                    <span class="chip ok">${tr('ofertaDisponible')}</span>
                  </div>
                  <p style="font-size:var(--t-sm);margin:0 0 var(--e3);">
                    Asegure el desembolso de su vivienda. Cubre el 100% de la deuda en caso de imprevistos sin trámites adicionales.
                  </p>
                  <div style="font-size:var(--t-xl);font-weight:800;color:var(--primario);margin-bottom:var(--e3);">
                    + ${fmtMoneda(c.primaFinal)} <span style="font-size:var(--t-xs);color:var(--texto-sec);font-weight:normal;">/ mes en su cuota</span>
                  </div>
                  
                  ${
                    state.socio.ofertaAceptada
                      ? `<div class="chip ok" style="padding:10px 16px;font-size:var(--t-sm);font-weight:700;">${tr('ofertaAceptadaExito')}</div>`
                      : `<div style="display:flex;gap:var(--e3);">
                          <button type="button" class="btn btn-primario" id="btnAceptarOfertaSocio">
                            ${tr('agregarSeguro')}
                          </button>
                          <button type="button" class="btn btn-secundario" id="btnRechazarOfertaSocio">
                            ${tr('masTarde')}
                          </button>
                        </div>`
                  }
                </div>
              `
                  : `
                <div class="aviso atencion">
                  ${window.ICONOS.info(24)}
                  <div>
                    <strong>${tr('ofertaNoDisponible')}</strong>
                    <p style="margin:2px 0;">${tr('ofertaNoDisponibleTexto')}</p>
                  </div>
                </div>
              `
              }
            </div>
          </section>
        </div>

        <aside class="pila">
          <section class="panel">
            <header>
              <h4>Simulación de Escenarios</h4>
            </header>
            <div class="contenido pila">
              <p style="font-size:var(--t-xs);color:var(--texto-sec);margin:0;">
                Pruebe cómo reacciona la interfaz del banco ante la disponibilidad del servicio:
              </p>
              
              <div style="display:flex;gap:var(--e2);">
                <button type="button" class="btn ${state.socio.ofertaDisponible ? 'btn-primario' : 'btn-secundario'}" id="btnOfertaActiva" style="flex:1;min-height:36px;font-size:12px;">
                  ✓ Oferta disponible
                </button>
                <button type="button" class="btn ${!state.socio.ofertaDisponible ? 'btn-primario' : 'btn-secundario'}" id="btnOfertaInactiva" style="flex:1;min-height:36px;font-size:12px;">
                  ✗ No disponible
                </button>
              </div>

              <div style="margin-top:var(--e3);font-size:var(--t-xs);color:var(--texto-sec);line-height:1.6;">
                <strong>Beneficio para el usuario:</strong> Cuando el servicio de seguro está disponible, se activa con 1 clic en la solicitud. Si no estuviera disponible, el crédito hipotecario continúa su curso normal sin bloquear al cliente.
              </div>
            </div>
          </section>
        </aside>
      </div>
    `;
  }

  // --- Renderizado Maestro ---
  function render() {
    renderCabecera();

    const stepperWrapper = document.getElementById('stepperWrapper');
    const contenidoVista = document.getElementById('contenidoVista');
    if (!contenidoVista) return;

    // Si la sesión NO está iniciada, mostrar pantalla de login W1
    if (!state.sesionIniciada) {
      if (stepperWrapper) stepperWrapper.style.display = 'none';
      contenidoVista.innerHTML = renderLogin();
    } else {
      if (stepperWrapper) {
        stepperWrapper.style.display = state.pestana === 'cotizador' ? 'block' : 'none';
        if (state.pestana === 'cotizador') renderStepper();
      }

      if (state.pestana === 'cotizador') {
        if (state.paso === 1) contenidoVista.innerHTML = renderPaso1();
        else if (state.paso === 2) contenidoVista.innerHTML = renderPaso2();
        else if (state.paso === 3) contenidoVista.innerHTML = renderPaso3();
        else if (state.paso === 4) contenidoVista.innerHTML = renderPaso4();
      } else if (state.pestana === 'gestion') {
        contenidoVista.innerHTML = renderGestion();
      } else if (state.pestana === 'socios') {
        contenidoVista.innerHTML = renderSocios();
      }
    }

    enlazarEventos();
  }

  // --- Enlace de Eventos Interactivos ---
  function enlazarEventos() {
    // Evento de Login
    const formLoginWeb = document.getElementById('formLoginWeb');
    if (formLoginWeb) {
      formLoginWeb.addEventListener('submit', (e) => {
        e.preventDefault();
        state.sesionIniciada = true;
        window.sessionStorage.setItem('solventa_web_auth', 'true');
        render();
      });
    }

    const btnIniciarSesionWeb = document.getElementById('btnIniciarSesionWeb');
    if (btnIniciarSesionWeb) {
      btnIniciarSesionWeb.addEventListener('click', (e) => {
        e.preventDefault();
        state.sesionIniciada = true;
        window.sessionStorage.setItem('solventa_web_auth', 'true');
        render();
      });
    }

    const linkOlvideClave = document.getElementById('linkOlvideClave');
    if (linkOlvideClave) {
      linkOlvideClave.addEventListener('click', (e) => {
        e.preventDefault();
        alert(tr('recuperarClaveMsg'));
      });
    }

    // Evento de Logout
    const btnCerrarSesionWeb = document.getElementById('btnCerrarSesionWeb');
    if (btnCerrarSesionWeb) {
      btnCerrarSesionWeb.addEventListener('click', () => {
        state.sesionIniciada = false;
        window.sessionStorage.removeItem('solventa_web_auth');
        render();
      });
    }

    // Paso 1
    const inpDoc = document.getElementById('inpDoc');
    if (inpDoc) inpDoc.addEventListener('input', (e) => (state.cliente.documento = e.target.value));

    const inpNom = document.getElementById('inpNom');
    if (inpNom) inpNom.addEventListener('input', (e) => (state.cliente.nombre = e.target.value));

    const inpEdad = document.getElementById('inpEdad');
    if (inpEdad) inpEdad.addEventListener('input', (e) => (state.cliente.edad = parseInt(e.target.value, 10) || 35));

    const inpTel = document.getElementById('inpTel');
    if (inpTel) inpTel.addEventListener('input', (e) => (state.cliente.telefono = e.target.value));

    const inpEnt = document.getElementById('inpEnt');
    if (inpEnt) inpEnt.addEventListener('input', (e) => (state.cliente.entidad = e.target.value));

    const inpMonto = document.getElementById('inpMonto');
    if (inpMonto) {
      inpMonto.addEventListener('input', (e) => {
        state.cliente.monto = parseFloat(e.target.value) || 0;
        const small = inpMonto.nextElementSibling;
        if (small) small.textContent = fmtMoneda(state.cliente.monto);
      });
    }

    const inpPlazo = document.getElementById('inpPlazo');
    if (inpPlazo) inpPlazo.addEventListener('input', (e) => (state.cliente.plazo = parseInt(e.target.value, 10) || 180));

    const btnIrPaso2 = document.getElementById('btnIrPaso2');
    if (btnIrPaso2) btnIrPaso2.addEventListener('click', () => { state.paso = 2; render(); });

    // Paso 2
    const chkConsentimiento = document.getElementById('chkConsentimiento');
    if (chkConsentimiento) {
      chkConsentimiento.addEventListener('change', (e) => {
        state.consentimiento.otorgado = e.target.checked;
      });
    }

    const btnSimularOtp = document.getElementById('btnSimularOtp');
    if (btnSimularOtp) {
      btnSimularOtp.addEventListener('click', () => {
        state.consentimiento.otpIngresado = '417902';
        state.consentimiento.otpValido = true;
        render();
      });
    }

    const inpOtp = document.getElementById('inpOtp');
    if (inpOtp) {
      inpOtp.addEventListener('input', (e) => {
        state.consentimiento.otpIngresado = e.target.value;
        state.consentimiento.otpValido = e.target.value.length >= 6;
      });
    }

    const btnIrPaso3 = document.getElementById('btnIrPaso3');
    if (btnIrPaso3) {
      btnIrPaso3.addEventListener('click', () => {
        if (!state.consentimiento.otorgado) {
          alert('Debe marcar la casilla de consentimiento informado para consultar las fuentes.');
          return;
        }
        state.paso = 3;
        render();
      });
    }

    const btnVolverPaso1 = document.getElementById('btnVolverPaso1');
    if (btnVolverPaso1) btnVolverPaso1.addEventListener('click', () => { state.paso = 1; render(); });

    // Paso 3
    const btnReintentarOF = document.getElementById('btnReintentarOF');
    if (btnReintentarOF) {
      btnReintentarOF.addEventListener('click', () => {
        window.SolventaDB.setDemoConfig('modoDegradadoForzado', false);
        render();
      });
    }

    const btnIrPaso4 = document.getElementById('btnIrPaso4');
    if (btnIrPaso4) {
      btnIrPaso4.addEventListener('click', () => {
        state.paso = 4;
        render();
      });
    }

    const btnVolverPaso2 = document.getElementById('btnVolverPaso2');
    if (btnVolverPaso2) btnVolverPaso2.addEventListener('click', () => { state.paso = 2; render(); });

    // Paso 4
    const btnEjecutarPago = document.getElementById('btnEjecutarPago');
    if (btnEjecutarPago) {
      btnEjecutarPago.addEventListener('click', () => {
        const c = calcularCotizacion();
        const nueva = window.SolventaDB.emitirPoliza({
          clienteDocumento: state.cliente.documento,
          clienteNombre: state.cliente.nombre,
          montoAsegurado: c.monto,
          primaMensual: c.primaFinal,
          moneda: window.REGIONES[state.region].moneda,
          socio: state.cliente.entidad,
          idempotencyKey: state.emision.referenciaSegura,
          desglose: c.desglose,
        });
        state.emision.polizaEmitida = nueva;
        state.gestion.polizaSeleccionadaId = nueva.id;
        render();
      });
    }

    const btnPedirRevision = document.getElementById('btnPedirRevision');
    if (btnPedirRevision) {
      btnPedirRevision.addEventListener('click', () => {
        state.emision.rechazoManualSolicitado = true;
        render();
      });
    }

    const btnVerEnGestion = document.getElementById('btnVerEnGestion');
    if (btnVerEnGestion) {
      btnVerEnGestion.addEventListener('click', () => {
        state.pestana = 'gestion';
        render();
      });
    }

    const btnNuevaCotizacion = document.getElementById('btnNuevaCotizacion');
    if (btnNuevaCotizacion) {
      btnNuevaCotizacion.addEventListener('click', () => {
        state.paso = 1;
        state.emision.polizaEmitida = null;
        render();
      });
    }

    const btnVolverPaso3 = document.getElementById('btnVolverPaso3');
    if (btnVolverPaso3) btnVolverPaso3.addEventListener('click', () => { state.paso = 3; render(); });

    // Gestión
    const inpBuscarGestion = document.getElementById('inpBuscarGestion');
    if (inpBuscarGestion) {
      inpBuscarGestion.addEventListener('input', (e) => {
        state.gestion.filtroTexto = e.target.value;
        render();
      });
    }

    const selFiltroEstado = document.getElementById('selFiltroEstado');
    if (selFiltroEstado) {
      selFiltroEstado.addEventListener('change', (e) => {
        state.gestion.filtroEstado = e.target.value;
        render();
      });
    }

    document.querySelectorAll('[data-seleccionar-poliza]').forEach((fila) => {
      fila.addEventListener('click', () => {
        state.gestion.polizaSeleccionadaId = fila.dataset.seleccionarPoliza;
        render();
      });
    });

    const tabDetCoberturas = document.getElementById('tabDetCoberturas');
    if (tabDetCoberturas) {
      tabDetCoberturas.addEventListener('click', () => {
        state.gestion.tabDetalle = 'coberturas';
        render();
      });
    }

    const tabDetSiniestros = document.getElementById('tabDetSiniestros');
    if (tabDetSiniestros) {
      tabDetSiniestros.addEventListener('click', () => {
        state.gestion.tabDetalle = 'siniestros';
        render();
      });
    }

    // Socios
    const btnAceptarOfertaSocio = document.getElementById('btnAceptarOfertaSocio');
    if (btnAceptarOfertaSocio) {
      btnAceptarOfertaSocio.addEventListener('click', () => {
        state.socio.ofertaAceptada = true;
        render();
      });
    }

    const btnRechazarOfertaSocio = document.getElementById('btnRechazarOfertaSocio');
    if (btnRechazarOfertaSocio) {
      btnRechazarOfertaSocio.addEventListener('click', () => {
        state.socio.ofertaAceptada = false;
        render();
      });
    }

    const btnOfertaActiva = document.getElementById('btnOfertaActiva');
    if (btnOfertaActiva) {
      btnOfertaActiva.addEventListener('click', () => {
        state.socio.ofertaDisponible = true;
        state.socio.ofertaAceptada = false;
        render();
      });
    }

    const btnOfertaInactiva = document.getElementById('btnOfertaInactiva');
    if (btnOfertaInactiva) {
      btnOfertaInactiva.addEventListener('click', () => {
        state.socio.ofertaDisponible = false;
        render();
      });
    }

    // Stepper click directo
    document.querySelectorAll('[data-ir-paso]').forEach((elem) => {
      elem.addEventListener('click', () => {
        state.paso = parseInt(elem.dataset.irPaso, 10);
        render();
      });
    });
  }

  // --- Inicio Global ---
  function iniciar() {
    // Tabs de navegación
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.pestana = btn.dataset.pestana;
        render();
      });
    });

    // Selectores globales
    const selIdioma = document.getElementById('selIdioma');
    if (selIdioma) {
      selIdioma.addEventListener('change', (e) => {
        state.idioma = e.target.value;
        render();
      });
    }

    const selRegion = document.getElementById('selRegion');
    if (selRegion) {
      selRegion.addEventListener('change', (e) => {
        state.region = e.target.value;
        state.cliente.monto = window.REGIONES[state.region].montoBase;
        render();
      });
    }

    const btnTema = document.getElementById('btnTema');
    if (btnTema) {
      btnTema.addEventListener('click', () => {
        state.tema = state.tema === 'oscuro' ? 'claro' : 'oscuro';
        render();
      });
    }

    // Suscripción a la base de datos compartida
    window.SolventaDB.subscribe(() => {
      render();
    });

    render();
  }

  window.addEventListener('DOMContentLoaded', iniciar);
})();


const parametros = new URLSearchParams(location.search);
const estado = {
  canal: parametros.get('canal') === 'movil' ? 'movil' : 'web',
  idioma: parametros.get('idioma') === 'en' ? 'en' : 'es',
  region: ['CO', 'MX', 'CL', 'PE'].includes(parametros.get('region')) ? parametros.get('region') : 'CO',
  pantalla: Math.max(0, Number(parametros.get('pantalla') || 0)),
  tema: parametros.get('tema') === 'oscuro' ? 'oscuro' : 'claro',
  dispositivo: parametros.get('dispositivo') === 'android' ? 'android' : 'ios',
};

/* Medidas reales de los frames. Escritorio 16:10; iPhone 14/15 19,5:9; Android 20:9. */
const DISPOSITIVOS = {
  escritorio: { w: 1440, h: 900, nombre: 'Escritorio', detalle: '1440 × 900 · 16:10' },
  ios: { w: 390, h: 844, nombre: 'iPhone 14/15', detalle: '390 × 844 · 19,5:9' },
  android: { w: 360, h: 800, nombre: 'Android', detalle: '360 × 800 · 20:9' },
};

const t = (clave) => TEXTOS[estado.idioma][clave] ?? clave;
const region = () => REGIONES[estado.region];

const dinero = (valor) =>
  new Intl.NumberFormat(region().locale, { style: 'currency', currency: region().moneda, maximumFractionDigits: 0 }).format(valor);
const fecha = (iso, estilo = 'long') =>
  new Intl.DateTimeFormat(region().locale, { dateStyle: estilo, timeStyle: 'short' }).format(new Date(iso));

const boton = (clave, { tipo = '', icono = '', ir = '' } = {}) =>
  `<button class="boton ${tipo}" type="button"${ir ? ` data-ir="${ir}"` : ''}>${icono ? ICONOS[icono](18) : ''}${t(clave)}</button>`;
const campo = (etiqueta, id, valor, tipo = 'text') =>
  `<div class="campo"><label for="${id}">${t(etiqueta)}</label><input id="${id}" type="${tipo}" value="${valor}" readonly></div>`;
const aviso = (clase, icono, titulo, cuerpo) =>
  `<div class="aviso ${clase}">${ICONOS[icono](20)}<div><strong>${titulo}</strong>${cuerpo}</div></div>`;
const dato = (etq, val) => `<li><span class="etq">${etq}</span><span class="val">${val}</span></li>`;

/* Pasos del recorrido de venta: sitúan al usuario dentro del flujo. */
function pasos(activo) {
  const nombres = ['pasoIdentificacion', 'pasoConsentimiento', 'pasoCotizacion', 'pasoEmision'];
  return `<div class="pasos">${nombres
    .map((n, i) => {
      const clase = i === activo ? 'activo' : i < activo ? 'hecho' : '';
      const marca = i < activo ? '✓' : i + 1;
      return `<span class="paso ${clase}"><span class="punto">${marca}</span>${t(n)}</span>${
        i < nombres.length - 1 ? '<span class="linea"></span>' : ''
      }`;
    })
    .join('')}</div>`;
}

const PANTALLAS_WEB = [
  { id: 'w1', grupo: 'gAcceso', hu: [], completa: true, cuerpo: () => `
    <div class="acceso-partido">
      <div class="acceso-marca">
        <div>
          <h4>${t('accesoTitulo')}</h4>
          <p>${t('accesoLema')}</p>
        </div>
      </div>
      <div class="acceso-formulario">
        <h4 style="font-size:var(--t-lg);margin-bottom:var(--e5)">${t('w1t')}</h4>
        ${campo('usuario', 'f-usuario', 'asesor@solventa.co', 'email')}
        ${campo('clave', 'f-clave', '••••••••', 'password')}
        <a href="#" style="color:var(--primario);font-size:var(--t-sm)">${t('olvide')}</a>
        <div class="acciones">${boton('entrar', { icono: 'llave', ir: 'w2' })}</div>
      </div>
    </div>` },

  { id: 'w2', grupo: 'gCotizacion', hu: ['HU-WEB-02'], titulo: 'w2tNuevo', desc: 'w2dNuevo', cuerpo: () => `
    ${pasos(0)}
    <div class="pila">
        <section class="panel">
          <header><h4>${t('seccionCliente')}</h4></header>
          <div class="contenido">
            <div class="dos-iguales">
              ${campo('documento', 'f-doc', '1.032.456.789')}
              ${campo('nombre', 'f-nom', 'María Fernanda Ruiz')}
              ${campo('edad', 'f-edad', '35')}
              ${campo('telefono', 'f-tel', '+57 310 555 4417')}
            </div>
          </div>
        </section>
        <section class="panel">
          <header><h4>${t('seccionCredito')}</h4></header>
          <div class="contenido">
            <div class="tres-columnas">
              ${campo('entidad', 'f-ent', 'Banco Aliado S.A.')}
              ${campo('monto', 'f-monto', dinero(region().monto))}
              ${campo('plazo', 'f-plazo', '180')}
            </div>
          </div>
        </section>
        <div class="acciones" style="justify-content:flex-end;margin-top:var(--e4)">${boton('continuar', { ir: 'w3' })}</div>
    </div>` },

  { id: 'w3', grupo: 'gCotizacion', hu: ['HU-WEB-01'], titulo: 'w3tNuevo', desc: 'w3dNuevo', cuerpo: () => `
    ${pasos(1)}
    <p class="contexto-cliente">María F. Ruiz · CC 1.032.456.789 · ${t('vidaHipotecario')}</p>
    <div class="dos-columnas">
      <div class="pila">
        <section class="panel">
          <header><h4>${t('datosConsultados')}</h4><span class="chip neutro">3</span></header>
          <div class="contenido pila">
            ${[['fuenteOF', 'detalleOF', 'enchufe'], ['fuenteOD', 'detalleOD', 'globo'], ['fuenteKYC', 'detalleKYC', 'candado']]
              .map(([tit, det, ic]) => `
              <div style="display:flex;gap:var(--e3);align-items:flex-start">
                <span style="color:var(--primario);flex:none">${ICONOS[ic](20)}</span>
                <div><strong style="font-size:var(--t-sm)">${t(tit)}</strong>
                  <p class="pista" style="margin:2px 0 0">${t(det)}</p></div>
              </div>`).join('')}
          </div>
        </section>
        <section class="panel">
          <header><h4>${t('autorizaCliente')}</h4><span class="chip aviso">${t('esperandoCliente')}</span></header>
          <div class="contenido">
            <p style="font-size:var(--t-sm);margin:0 0 var(--e3)">${t('autorizaTexto')}</p>
            <div class="aviso info" style="margin:0">${ICONOS.movil(20)}
              <div><strong>${t('verificacion')}</strong>${t('otpEnviado')}</div></div>
          </div>
        </section>
        <p class="pista">${t('baseLegal')}</p>
      </div>
      <aside class="pila">
        <section class="panel plano">
          <header><h4>${t('resumenSolicitud')}</h4></header>
          <div class="contenido">
            <div class="resumen-lateral">
              <div class="fila"><span class="etq">${t('finalidad')}</span><span class="val">${t('finalidadValor')}</span></div>
              <div class="fila"><span class="etq">${t('vigenciaEtq')}</span><span class="val">12 ${estado.idioma === 'es' ? 'meses' : 'months'}</span></div>
            </div>
            <p class="seccion-titulo">${t('derechos')}</p>
            <ul class="lista-check">
              <li><span class="si">${ICONOS.check(18)}</span>${t('derecho1')}</li>
              <li><span class="si">${ICONOS.check(18)}</span>${t('derecho2')}</li>
            </ul>
          </div>
        </section>
        ${boton('cotizar', { tipo: 'ancho', icono: 'documento', ir: 'w4' })}
      </aside>
    </div>` },

  { id: 'w4', grupo: 'gCotizacion', hu: ['HU-WEB-03'], cuerpo: () => {
    const p = region().prima;
    const partes = [['tarifaBase', 0.62], ['ajusteRiesgo', 0.18], ['ajusteEdad', 0.11], ['impuestos', 0.09]];
    return `
    ${pasos(2)}
    <div class="dos-columnas">
      <div class="pila">
        <section class="panel acento">
          <header><h4>${t('primaMensual')}</h4><span class="chip ok">${t('perfilCompleto')}</span></header>
          <div class="contenido">
            <div class="hero-precio" style="margin-top:0">
              <span class="valor">${dinero(p)}</span><span class="unidad">/ ${t('primaMensual')}</span>
              <span class="comparativo">
                <s>${dinero(p * 1.22)}</s> ${t('ahorro')}: <strong>${dinero(p * 0.22)}</strong>
              </span>
            </div>
            <p class="pista">${ICONOS.reloj(14)} ${t('calculadaEn')} 0,2 s · ${t('origenDato').split(' · ')[0]}</p>
            <ul class="desglose">${partes.map(([clave, f]) => `
              <li><div class="fila"><span>${t(clave)}</span><strong>${dinero(p * f)}</strong></div>
              <div class="barra"><span style="width:${f * 100}%"></span></div></li>`).join('')}
            </ul>
          </div>
        </section>
      </div>
      <aside class="pila">
        <section class="panel">
          <header><h4>${t('resumenRiesgo')}</h4></header>
          <div class="contenido pila">
            <div>
              <p class="seccion-titulo" style="margin-top:0">${t('nivelRiesgoEtq')}</p>
              <div class="escala-riesgo"><i class="activo"></i><i></i><i></i></div>
              <strong style="font-size:var(--t-sm)">${t('nivelBajo')}</strong>
            </div>
            <div>
              <p class="seccion-titulo" style="margin-top:0">${t('explicacionPrecio')}</p>
              <ul class="lista-check">
                <li><span class="si">${ICONOS.check(18)}</span>${t('factor1')}</li>
                <li><span class="si">${ICONOS.check(18)}</span>${t('factor2')}</li>
              </ul>
            </div>
            <div>
              <p class="seccion-titulo" style="margin-top:0">${t('incluye')}</p>
              <ul class="lista-check">
                <li><span class="si">${ICONOS.check(18)}</span>${t('cobertura1')}</li>
                <li><span class="si">${ICONOS.check(18)}</span>${t('cobertura2')}</li>
              </ul>
            </div>
          </div>
        </section>
        <p class="pista">${t('vigenciaOferta')}: ${fecha('2026-09-25T18:00:00', 'medium')}</p>
        ${boton('emitir', { tipo: 'ancho', icono: 'escudo', ir: 'w6' })}
        ${boton('verDegradada', { tipo: 'secundario ancho', icono: 'alerta', ir: 'w5' })}
      </aside>
    </div>`; } },

  { id: 'w5', grupo: 'gCotizacion', hu: ['HU-WEB-04'], cuerpo: () => {
    const base = region().prima;
    return `
    ${pasos(2)}
    <p class="contexto-cliente">${ICONOS.alerta(15)} ${t('avisoDegradado')}</p>
    <div class="dos-columnas">
      <div class="pila">
        <section class="panel">
          <header><h4>${t('impactoPrecio')}</h4><span class="chip aviso">+4 %</span></header>
          <div class="contenido">
            <div class="dos-iguales">
              <div class="kpi"><span class="etq">${t('conPerfilCompleto')}</span>
                <span class="val" style="color:var(--texto-sec)">${dinero(base)}</span></div>
              <div class="kpi"><span class="etq">${t('conPerfilParcial')}</span>
                <span class="val">${dinero(base * 1.04)}</span>
                <span class="delta baja">+ ${dinero(base * 0.04)}</span></div>
            </div>
            <p class="pista" style="margin-top:var(--e3)">${t('impactoDetalle')}</p>
          </div>
        </section>
        <section class="panel">
          <header><h4>${t('queFalta')}</h4></header>
          <div class="contenido">
            <ul class="datos">
              <li><span class="etq">${t('faltaOF')}</span><span class="val"><span class="chip aviso">${t('noRespondio')}</span></span></li>
              <li><span class="etq">${t('fuenteOD')}</span><span class="val"><span class="chip ok">${t('consultada')}</span></span></li>
              <li><span class="etq">${t('fuenteKYC')}</span><span class="val"><span class="chip ok">${t('consultada')}</span></span></li>
            </ul>
          </div>
        </section>
      </div>
      <aside class="pila">
        <section class="panel">
          <header><h4>${t('resumenRiesgo')}</h4><span class="chip aviso">${t('degradado')}</span></header>
          <div class="contenido resumen-lateral">
            <div class="fila"><span class="etq">${t('origenDato').split(':')[0]}</span><span class="val">${t('origenParcial')}</span></div>
            <div class="fila"><span class="etq">${t('antiguedad').split(':')[0]}</span><span class="val">3 ${estado.idioma === 'es' ? 'días' : 'days'}</span></div>
          </div>
        </section>
        ${boton('emitir', { tipo: 'ancho', icono: 'escudo', ir: 'w6' })}
      </aside>
    </div>`; } },

  { id: 'w6', grupo: 'gEmision', hu: ['HU-WEB-05', 'HU-WEB-06', 'HU-WEB-07'], cuerpo: () => {
    const p = region().prima;
    return `
    ${pasos(3)}
    <div class="dos-columnas">
      <div class="pila">
        <section class="panel">
          <header><h4>${t('pasosEmision')}</h4><span class="chip ok">3 / 4</span></header>
          <div class="contenido">
            <ol class="linea-tiempo" style="margin-top:0">
              <li class="hecho">${t('pasoCobro')}<span class="cuando">${t('completado')}</span></li>
              <li class="hecho">${t('pasoFirma')}<span class="cuando">${t('completado')}</span></li>
              <li class="hecho">${t('pasoPoliza')}<span class="cuando">${t('completado')}</span></li>
              <li class="actual">${t('pasoEnvio')}<span class="cuando">${t('pendiente')}</span></li>
            </ol>
          </div>
        </section>
        ${aviso('info', 'candado', t('sinDuplicados'), t('sinDuplicar'))}
        ${aviso('error', 'equis', t('rechazoTitulo'),
          `${t('rechazoMotivo')} <a href="#" class="enlace-aviso">${t('solicitarRevision')}</a>`)}
      </div>
      <aside class="pila">
        <section class="panel acento">
          <header><h4>${t('resumenCompra')}</h4></header>
          <div class="contenido resumen-lateral">
            <div class="fila"><span class="etq">${t('productoSeguro')}</span><span class="val">${t('vidaHipotecario')}</span></div>
            <div class="fila"><span class="etq">${t('metodoPago')}</span><span class="val">${t('tarjeta')}</span></div>
            <div class="total"><span class="etq">${t('totalPagar')}</span><span class="val">${dinero(p)}</span></div>
          </div>
        </section>
        ${aviso('exito', 'check', t('polizaEmitida'), 'POL-2026-004182')}
        ${boton('pagar', { tipo: 'ancho', icono: 'tarjeta', ir: 'w7' })}
      </aside>
    </div>`; } },

  { id: 'w7', grupo: 'gGestion', hu: ['HU-WEB-08', 'HU-WEB-09'], cuerpo: () => `
    <div class="dos-columnas">
      <div class="pila">
        <section class="panel">
          <header><h4>${t('buscar')}</h4><span class="chip neutro">${t('resultadosEncontrados')}</span></header>
          <div class="contenido">
            <div style="display:flex;gap:var(--e3);margin-bottom:var(--e4)">
              <div style="flex:1" class="campo"><input value="1.032.456.789" readonly aria-label="${t('criterio')}"></div>
              ${boton('buscar', { icono: 'buscar' })}
            </div>
            <table class="tabla">
              <thead><tr><th>${t('poliza')}</th><th>${t('ramo')}</th><th>${t('inicio')}</th><th>${t('estado')}</th></tr></thead>
              <tbody>
                <tr class="seleccionada"><td><strong>POL-2026-004182</strong></td><td>${t('vidaHipotecario')}</td><td>${fecha('2026-09-01T08:00:00', 'medium').split(',')[0]}</td><td><span class="chip ok">${t('vigente')}</span></td></tr>
                <tr><td>POL-2026-003918</td><td>${t('proteccionPagos')}</td><td>${fecha('2026-08-14T08:00:00', 'medium').split(',')[0]}</td><td><span class="chip neutro">${t('pendiente')}</span></td></tr>
                <tr><td>POL-2025-001204</td><td>${t('vidaHipotecario')}</td><td>${fecha('2025-11-03T08:00:00', 'medium').split(',')[0]}</td><td><span class="chip neutro">${t('rechazada')}</span></td></tr>
              </tbody>
            </table>
          </div>
        </section>
        <section class="panel">
          <header><h4>POL-2026-004182</h4><span class="chip ok">${t('vigente')}</span></header>
          <div class="contenido">
            <div class="pestanas">
              <span class="activa">${t('tabCoberturas')}</span><span>${t('tabSiniestros2')}</span>
            </div>
            <div class="dos-iguales">
              <ul class="datos">
                ${dato(t('sumaAsegurada'), dinero(region().monto))}
                ${dato(t('primaMensual'), dinero(region().prima))}
              </ul>
              <ul class="datos">
                ${dato(t('vigenciaPoliza'), `${fecha('2026-09-01T08:00:00', 'medium').split(',')[0]} — ${fecha('2027-09-01T08:00:00', 'medium').split(',')[0]}`)}
                ${dato(t('siniestros'), t('sinSiniestros'))}
              </ul>
            </div>
          </div>
        </section>
      </div>
      <aside class="pila">
        <section class="panel plano">
          <header><h4>${t('filtros')}</h4></header>
          <div class="contenido pila">
            ${campo('socio', 'f-soc', 'Banco Aliado S.A.')}
            <p class="pista">${ICONOS.candado(14)} ${t('alcanceConsulta')}</p>
          </div>
        </section>
      </aside>
    </div>` },

  { id: 'w8', grupo: 'gSocios', hu: ['HU-WEB-10', 'HU-WEB-11', 'HU-WEB-12'],
    titulo: 'w8tNuevo', desc: 'w8dNuevo', canalExterno: true,

    // Dentro del marco solo va lo que el cliente del banco puede ver.
    cuerpo: () => `
    <p class="seccion-titulo" style="margin-top:0">${t('loQueVeCliente')}</p>
    <div class="dos-iguales">
      <section class="panel">
        <header><h4>${t('ofertaEmbebida')}</h4><span class="chip ok">${t('respuestaOk')}</span></header>
        <div class="contenido">
          <p style="font-size:var(--t-sm);color:var(--texto-sec);margin:0 0 var(--e3)">${t('ofertaTexto')}</p>
          <div class="hero-precio" style="margin:0">
            <span class="valor">${dinero(region().prima)}</span><span class="unidad">/ ${t('primaMensual')}</span>
          </div>
          <ul class="lista-check" style="margin-top:var(--e3)">
            <li><span class="si">${ICONOS.check(18)}</span>${t('cobertura1')}</li>
            <li><span class="si">${ICONOS.check(18)}</span>${t('cobertura2')}</li>
          </ul>
          <div class="acciones">${boton('aceptarOferta', { ir: 'w6' })}${boton('masTarde', { tipo: 'secundario' })}</div>
          <p class="pista">${ICONOS.escudo(14)} Solventa · ${t('vidaHipotecario')}</p>
        </div>
      </section>
      <section class="panel">
        <header><h4>${t('ofertaEmbebida')}</h4><span class="chip aviso">${t('respuestaCuota')}</span></header>
        <div class="contenido">
          <div class="aviso atencion" style="margin-top:0">${ICONOS.info(20)}
            <div><strong>${t('ofertaNoDisponible')}</strong>${t('ofertaNoDisponibleTexto')}</div></div>
          <p class="pista">${ICONOS.escudo(14)} Solventa · ${t('vidaHipotecario')}</p>
        </div>
      </section>
    </div>`,

    // El contrato técnico se documenta fuera del dispositivo: el cliente nunca lo ve.
    anotacion: () => `
    <section class="panel plano anotacion">
      <header><h4>${ICONOS.enchufe(18)} ${t('contratoApi')}</h4><span class="chip neutro">HU-WEB-11 · HU-WEB-12</span></header>
      <div class="contenido tres-columnas">
        <div>
          <p class="seccion-titulo" style="margin-top:0">${t('respuestaOk')}</p>
          <ul class="datos">
            ${dato('HTTP', '<code>200</code>')}
            ${dato(t('referencia'), '<code>REF-99120</code>')}
            ${dato(t('tiempoRespuesta'), '118 ms')}
          </ul>
        </div>
        <div>
          <p class="seccion-titulo" style="margin-top:0">${t('reintentoSeguro')}</p>
          <ul class="datos">${dato(t('idIdempotencia'), '<code>c7f1…6b33</code>')}</ul>
          <p class="pista">${t('reintentoTexto')}</p>
        </div>
        <div>
          <p class="seccion-titulo" style="margin-top:0">${t('respuestaCuota')}</p>
          <ul class="datos">${dato('HTTP', '<code>429</code>')}${dato(t('proximoIntento'), '14:35')}</ul>
          <p class="pista">${t('cuotaMensual')}: 49.980 / 50.000</p>
        </div>
      </div>
      <div class="contenido dos-iguales" style="padding-top:0">
        <div>
          <p class="seccion-titulo" style="margin-top:0">${t('autenticacionSocio')}</p>
          <ul class="datos">${dato('API', '<code>sk_live_••••4417</code>')}</ul>
        </div>
        <div>
          <p class="seccion-titulo" style="margin-top:0">${t('aislamientoSocios')}</p>
          <p class="pista">${ICONOS.candado(14)} ${t('aislamientoTexto')}</p>
        </div>
      </div>
      <p class="pista nota-fuera">${ICONOS.info(14)} ${t('contratoApiNota')}</p>
    </section>`,
  },
];

const PANTALLAS_MOVIL = [
  { id: 'm1', grupo: 'gAcceso', hu: ['HU-MOV-01', 'HU-MOV-03'], centrado: true, cuerpo: () => `
    <div style="text-align:center">
      <span class="simbolo" style="width:52px;height:52px;border-radius:15px;display:inline-grid;place-items:center;
        background:linear-gradient(135deg,var(--marca-500),var(--acento));color:#fff">${ICONOS.escudo(26)}</span>
      <h4 style="font-size:var(--t-lg);margin:var(--e3) 0 0">${t('bienvenidaNeutra')}</h4>
    </div>
    <div class="huella">
      <button type="button" class="circulo" data-ir="m3" aria-label="${t('tocarSensor')}">${ICONOS.huella(46)}</button>
      <p style="margin:0">${t('tocarSensor')}</p>
    </div>
    ${boton('usarAlterno', { tipo: 'secundario ancho', ir: 'm2' })}
    <p class="pista" style="text-align:center;margin-top:var(--e4)">${ICONOS.candado(13)} ${t('cifrada')}</p>` },

  { id: 'm2', grupo: 'gAcceso', hu: ['HU-MOV-02'], cuerpo: () => `
    ${aviso('info', 'info', t('m2t'), t('m2d'))}
    ${campo('correo', 'm-user', 'maria.ruiz@correo.co', 'email')}
    ${campo('clave', 'm-clave', '••••••••', 'password')}
    ${campo('codigo', 'm-otp', '4 1 7 · 9 0 2')}
    <p class="pista">${ICONOS.reloj(13)} ${t('reenviarEn')} 00:42</p>
    ${boton('entrar', { tipo: 'ancho', ir: 'm3' })}
    ${boton('enviarCodigo', { tipo: 'secundario ancho' })}` },

  { id: 'm3', grupo: 'gBilletera', hu: ['HU-MOV-04', 'HU-MOV-05', 'HU-MOV-06'], cuerpo: () => `
    <p style="font-size:var(--t-md);font-weight:650;margin:0 0 var(--e3)">${t('saludoTrasAcceso')}</p>
    <div class="carne">
      <div class="marca-carne"><span>${ICONOS.escudo(16)} Solventa</span><span>${t('vidaHipotecario')}</span></div>
      <div class="numero">POL-2026-004182</div>
      <div style="font-size:var(--t-sm)">María Fernanda Ruiz</div>
      <div class="pie-carne"><span>${t('sumaAsegurada')}<br><strong>${dinero(region().monto)}</strong></span>
        <span>${t('vigenteHasta')}<br><strong>${fecha('2027-09-01T08:00:00', 'medium').split(',')[0]}</strong></span></div>
    </div>
    <p class="seccion-titulo">${t('misPolizas')}</p>
    <ul class="lista-movil">
      <li><span class="icono-bolsa">${ICONOS.escudo(18)}</span>
        <span class="crece"><strong>${t('vidaHipotecario')}</strong><span>POL-2026-004182</span></span>
        <span class="chip ok">${t('vigente')}</span></li>
      <li><span class="icono-bolsa">${ICONOS.documento(18)}</span>
        <span class="crece"><strong>${t('proteccionPagos')}</strong><span>POL-2026-003918</span></span>
        <span class="chip neutro">${t('pendiente')}</span></li>
    </ul>
    ${boton('reportarSiniestro', { tipo: 'ancho', icono: 'camara', ir: 'm5' })}
    ${boton('verSinConexion', { tipo: 'secundario ancho', icono: 'sinSenal', ir: 'm4' })}
    <p class="pista" style="margin-top:var(--e4)">${ICONOS.reloj(13)} ${t('ultimaSync')}: ${fecha('2026-09-11T07:42:00', 'short')}</p>` },

  { id: 'm4', grupo: 'gBilletera', hu: ['HU-MOV-07'], cuerpo: () => `
    ${aviso('atencion', 'sinSenal', t('sinConexion'), t('avisoOffline'))}
    <div class="carne" style="opacity:.85">
      <div class="marca-carne"><span>${ICONOS.escudo(16)} Solventa</span><span class="chip neutro" style="background:rgba(255,255,255,.2);color:#fff">${t('enCache')}</span></div>
      <div class="numero">POL-2026-004182</div>
      <div class="pie-carne"><span>${t('vigenteHasta')}<br><strong>${fecha('2027-09-01T08:00:00', 'medium').split(',')[0]}</strong></span></div>
    </div>
    <p class="seccion-titulo">${t('pendienteSync')}</p>
    <ul class="lista-movil">
      <li><span class="icono-bolsa">${ICONOS.camara(18)}</span>
        <span class="crece"><strong>${t('m5t')}</strong><span>${t('enCola')}</span></span>
        ${ICONOS.reloj(16)}</li>
    </ul>
    <p class="pista" style="margin-top:var(--e4)">${ICONOS.reloj(13)} ${t('ultimaSync')}: ${fecha('2026-09-11T07:42:00', 'short')}</p>` },

  { id: 'm5', grupo: 'gSiniestros', hu: ['HU-MOV-08'], cuerpo: () => `
    <div class="pasos" style="margin-bottom:var(--e3)">
      <span class="paso activo"><span class="punto">1</span>${t('pasoEvidencia')}</span><span class="linea"></span>
      <span class="paso"><span class="punto">2</span>${t('pasoDetalle')}</span><span class="linea"></span>
      <span class="paso"><span class="punto">3</span>${t('pasoEnviar')}</span>
    </div>
    <div class="marco-foto" style="aspect-ratio:2/1">${ICONOS.camara(28)}
      <span class="pista" style="position:absolute;bottom:6px;right:10px">${ICONOS.check(13)} ${t('foto1')}</span></div>
    ${boton('tomarFoto', { tipo: 'secundario ancho', icono: 'camara' })}
    <ul class="datos">
      ${dato(t('polizaAfectada'), `${t('vidaHipotecario')} · POL-2026-004182`)}
      ${dato(t('ubicacion'), '4.6512, −74.0568')}
      ${dato(t('fechaHora'), fecha('2026-09-11T09:15:00', 'short'))}
    </ul>
    <div class="campo"><label for="m-desc">${t('descripcion')}</label>
      <textarea id="m-desc" rows="2" readonly>Daño en la puerta del conductor.</textarea></div>
    ${boton('enviarReporte', { tipo: 'ancho', ir: 'm6' })}` },

  { id: 'm6', grupo: 'gSiniestros', hu: ['HU-MOV-09'], cuerpo: () => `
    ${aviso('atencion', 'sinSenal', t('enCola'), t('avisoCola'))}
    <div class="panel">
      <div class="contenido">
        <strong style="font-size:var(--t-sm)">${t('m5t')}</strong>
        <ul class="datos" style="margin-top:var(--e3)">
          ${dato(t('polizaAfectada'), 'POL-2026-004182')}
          ${dato(t('adjuntos'), `2 · 1,8 MB`)}
          ${dato(t('fechaHora'), fecha('2026-09-11T09:16:00', 'short'))}
        </ul>
        <div class="aviso info" style="margin-bottom:0">${ICONOS.candado(20)}
          <div><strong>${t('radicadoUnico')}</strong>${t('radicadoUnicoTexto')}</div></div>
      </div>
    </div>
    ${boton('verEstado', { tipo: 'ancho', ir: 'm7' })}` },

  { id: 'm7', grupo: 'gSiniestros', hu: ['HU-MOV-10', 'HU-MOV-11'], cuerpo: () => `
    <div class="panel acento">
      <div class="contenido" style="text-align:center">
        <p class="pista" style="margin:0">${t('radicado')}</p>
        <p style="font-size:var(--t-xl);font-weight:700;margin:var(--e1) 0">SIN-2026-00871</p>
        <span class="chip aviso">${t('enEvaluacion')}</span>
      </div>
    </div>
    <p class="seccion-titulo">${t('lineaTiempo')}</p>
    <ol class="linea-tiempo">
      <li class="hecho">${t('recibido')}<span class="cuando">${fecha('2026-09-11T09:16:00', 'short')}</span></li>
      <li class="actual">${t('asignado')}<span class="cuando">${t('enEvaluacion')}</span></li>
      <li>${t('resuelto')}</li>
    </ol>
` },
];

const pantallas = () => (estado.canal === 'web' ? PANTALLAS_WEB : PANTALLAS_MOVIL);

function pintarIndice(lista) {
  let grupoActual = null;
  const filas = lista.map((p, i) => {
    const encabezado = p.grupo !== grupoActual ? `<li class="grupo-titulo">${t(p.grupo)}</li>` : '';
    grupoActual = p.grupo;
    return `${encabezado}<li><button type="button" data-ir="${p.id}" aria-current="${i === estado.pantalla}">
      <span class="num">${i + 1}</span>${t(p.titulo || p.id + 't')}</button></li>`;
  });
  document.getElementById('indice').innerHTML = filas.join('');
}

function pintar() {
  document.documentElement.lang = estado.idioma;
  document.documentElement.dataset.tema = estado.tema;

  const fijos = {
    'titulo-producto': 'producto', 'subtitulo-producto': 'sinFuncionalidad',
    salto: 'saltar', 'rotulo-idioma': 'idioma', 'rotulo-region': 'region', 'rotulo-pantallas': 'pantallas',
  };
  for (const [id, clave] of Object.entries(fijos)) document.getElementById(id).textContent = t(clave);

  document.getElementById('tab-web').innerHTML = `${ICONOS.monitor(18)}${t('canalWeb')}`;
  document.getElementById('tab-movil').innerHTML = `${ICONOS.movil(18)}${t('canalMovil')}`;
  document.getElementById('tab-web').setAttribute('aria-selected', estado.canal === 'web');
  document.getElementById('tab-movil').setAttribute('aria-selected', estado.canal === 'movil');
  document.getElementById('tema').innerHTML = estado.tema === 'oscuro' ? ICONOS.sol(18) : ICONOS.luna(18);
  document.getElementById('tema').setAttribute('aria-label', estado.tema === 'oscuro' ? t('temaClaro') : t('temaOscuro'));

  document.getElementById('dispositivos').innerHTML =
    estado.canal === 'movil'
      ? ['ios', 'android'].map((d) =>
          `<button type="button" data-dispositivo="${d}" aria-pressed="${estado.dispositivo === d}">
             ${DISPOSITIVOS[d].nombre}</button>`).join('')
      : `<button type="button" aria-pressed="true" disabled>${DISPOSITIVOS.escritorio.nombre}</button>`;

  const lista = pantallas();
  if (estado.pantalla >= lista.length) estado.pantalla = 0;
  pintarIndice(lista);

  const p = lista[estado.pantalla];
  const disp = estado.canal === 'web' ? DISPOSITIVOS.escritorio : DISPOSITIVOS[estado.dispositivo];

  const menuApp = ['gCotizacion', 'gGestion']
    .map((g) => `<span class="${p.grupo === g ? 'activo' : ''}">${t(g)}</span>`).join('');

  const contenidoEscritorio = `
    <div class="marco marco-escritorio">
      <div class="navegador">
        <div class="semaforo"><i></i><i></i><i></i></div>
        <div class="url">${ICONOS.candado(12)} ${p.canalExterno ? 'banco-aliado.co/creditos/hipotecario' : 'app.solventa.co'}</div>
      </div>
      <div class="app">
        ${p.completa ? '' : `
        <div class="app-barra">
          <div class="app-marca">
            <span class="simbolo" ${p.canalExterno ? 'style="background:#1d4e89"' : ''}>${p.canalExterno ? ICONOS.tarjeta(18) : ICONOS.escudo(18)}</span>
            ${p.canalExterno ? 'Banco Aliado' : 'Solventa'}</div>
          <nav class="app-nav">${p.canalExterno ? '' : menuApp}</nav>
          <div class="app-usuario">
            <span>${p.canalExterno ? 'Carlos R. · Cliente' : p.grupo === 'gGestion' ? `Andrés L. · ${t('rolAnalista')}` : `María F. · ${t('asesorRol')}`}</span>
            <span class="avatar">${p.canalExterno ? 'CR' : p.grupo === 'gGestion' ? 'AL' : 'MR'}</span></div>
        </div>`}
        ${p.completa ? p.cuerpo() : `
        <div class="app-lienzo denso">
          <div class="encabezado-pantalla">
            <div>
              <h3>${t(p.titulo || p.id + 't')}</h3>
              <p class="subtitulo">${t(p.desc || p.id + 'd')}</p>
            </div>
          </div>
          ${p.cuerpo()}
        </div>`}
      </div>
    </div>`;

  const contenidoMovil = `
    <div class="marco marco-movil-disp">
      <div class="pantalla-movil">
        <div class="estado-ios">
          <span>9:41</span>
          <span class="senales">${ICONOS.reloj(13)} 82 %</span>
        </div>
        <div class="app-movil-barra"><h3>${t(p.titulo || p.id + 't')}</h3></div>
        <div class="movil-lienzo${p.centrado ? ' centrado' : ''}">${p.cuerpo()}</div>
        <div class="tabbar-movil">
          <div class="${['m3', 'm4'].includes(p.id) ? 'activo' : ''}">${ICONOS.cartera(20)}${t('tabBilletera')}</div>
          <div class="${['m5', 'm6', 'm7'].includes(p.id) ? 'activo' : ''}">${ICONOS.camara(20)}${t('tabSiniestros')}</div>
          <div class="${['m1', 'm2'].includes(p.id) ? 'activo' : ''}">${ICONOS.candado(20)}${t('tabCuenta')}</div>
        </div>
        <div class="indicador-inicio"></div>
      </div>
    </div>`;

  document.getElementById('pantalla').innerHTML = `
    <div class="info-pantalla">
      <div>
        <span class="contador">${estado.idioma === 'es' ? 'Pantalla' : 'Screen'} ${estado.pantalla + 1} / ${lista.length}</span>
        <h2>${t(p.grupo)}</h2>
      </div>
      <div class="historias">
        ${p.hu.length
          ? `<span class="etiqueta">${t('cubre')}</span>${p.hu.map((h) => `<span class="hu">${h}</span>`).join('')}`
          : `<span class="hu" style="background:var(--n-100);color:var(--texto-sec)">${t('pantallaSoporte')}</span>`}
        <span class="medidas">${disp.detalle}</span>
      </div>
    </div>
    <div class="marco-envoltura" style="--w:${disp.w}px; --h:${disp.h}px; --escala:1">
      ${estado.canal === 'web' ? contenidoEscritorio : contenidoMovil}
    </div>
    ${p.anotacion ? p.anotacion() : ''}`;

  ajustarEscala(disp);

  document.getElementById('usabilidad').innerHTML = [
    ['globo', 'u1t', 'u1'], ['mapa', 'u2t', 'u2'], ['accesible', 'u3t', 'u3'],
  ].map(([ic, titulo, texto]) =>
    `<article><h3>${ICONOS[ic](18)}${t(titulo)}</h3><p>${t(texto)}</p></article>`).join('');

  document.getElementById('cobertura').innerHTML = `
    <article>
      <h3>${ICONOS.escudo(18)}${t('coberturaTitulo')}</h3>
      <p>${t('coberturaTexto')}</p>
      <div class="cobertura-cuenta">
        <span><strong>12</strong> ${t('canalWeb')}</span>
        <span><strong>11</strong> ${t('canalMovil')}</span>
        <span><strong>23</strong> / 23</span>
      </div>
    </article>`;
}

/* El frame se dibuja a tamaño real y se reduce para caber en el espacio disponible. */
function navegarA(id) {
  const canal = PANTALLAS_WEB.some((p) => p.id === id) ? 'web' : 'movil';
  const lista = canal === 'web' ? PANTALLAS_WEB : PANTALLAS_MOVIL;
  estado.canal = canal;
  estado.pantalla = lista.findIndex((p) => p.id === id);
  pintar();
}

function ajustarEscala(disp) {
  const envoltura = document.querySelector('.marco-envoltura');
  if (!envoltura) return;
  // Se colapsa la envoltura antes de medir: con el frame a tamaño real el contenedor
  // se desborda y devolvería un ancho disponible falso.
  envoltura.style.setProperty('--escala', '0');
  const disponible = envoltura.parentElement.clientWidth;
  const desdeArriba = envoltura.getBoundingClientRect().top;
  const alturaMaxima = Math.max(420, window.innerHeight - desdeArriba - 32);
  const escala = Math.min(1, disponible / disp.w, alturaMaxima / disp.h);
  envoltura.style.setProperty('--escala', escala.toFixed(4));
}

window.addEventListener('resize', () => {
  const disp = estado.canal === 'web' ? DISPOSITIVOS.escritorio : DISPOSITIVOS[estado.dispositivo];
  ajustarEscala(disp);
});

document.addEventListener('click', (e) => {
  const ir = e.target.closest('[data-ir]');
  if (ir) { navegarA(ir.dataset.ir); return; }
  const canal = e.target.closest('#tab-web, #tab-movil');
  if (canal) { estado.canal = canal.id === 'tab-web' ? 'web' : 'movil'; estado.pantalla = 0; pintar(); return; }
  if (e.target.closest('#tema')) { estado.tema = estado.tema === 'oscuro' ? 'claro' : 'oscuro'; pintar(); return; }
  const disp = e.target.closest('[data-dispositivo]');
  if (disp) { estado.dispositivo = disp.dataset.dispositivo; pintar(); }
});

document.getElementById('sel-idioma').addEventListener('change', (e) => { estado.idioma = e.target.value; pintar(); });
document.getElementById('sel-region').addEventListener('change', (e) => { estado.region = e.target.value; pintar(); });

document.getElementById('sel-region').innerHTML = Object.entries(REGIONES)
  .map(([k, v]) => `<option value="${k}"${k === estado.region ? ' selected' : ''}>${v.etiqueta} · ${v.moneda}</option>`).join('');
document.getElementById('sel-idioma').value = estado.idioma;
document.querySelector('.marca .simbolo').innerHTML = ICONOS.escudo(20);

pintar();

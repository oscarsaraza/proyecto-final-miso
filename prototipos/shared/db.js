/* ============================================================================
   Solventa · Almacén de datos compartido y reactivo para la PoC
   Persistencia en localStorage con sincronización automática entre pestañas
   vía 'storage' event y BroadcastChannel.
   ========================================================================= */

const SOLVENTA_STORAGE_KEY = 'solventa_poc_data_v1';
const SOLVENTA_CHANNEL_NAME = 'solventa_poc_sync_channel';

// Datos iniciales precargados representativos del caso Solventa
const DATOS_SEMILLA = {
  cliente: {
    documento: '1.032.456.789',
    tipoDocumento: 'CC',
    nombre: 'María Fernanda Ruiz',
    edad: 35,
    telefono: '+57 310 555 4417',
    correo: 'maria.ruiz@correo.co',
    ciudad: 'Bogotá, D.C.',
    ocupacion: 'Ingeniera de sistemas',
    ingresoMensual: 9500000,
  },
  polizas: [
    {
      id: 'POL-2026-004182',
      ramo: 'vidaHipotecario',
      ramoNombre: 'Vida Hipotecario',
      clienteDocumento: '1.032.456.789',
      clienteNombre: 'María Fernanda Ruiz',
      socio: 'Banco Aliado S.A.',
      montoAsegurado: 250000000,
      primaMensual: 68400,
      moneda: 'COP',
      estado: 'vigente', // vigente, pendiente, rechazada
      fechaInicio: '2026-09-01T08:00:00',
      fechaVigencia: '2027-09-01T08:00:00',
      idempotencyKey: 'c7f1a8e2-5b91-4e20-8a42-8819ef36b331',
      coberturas: [
        { nombre: 'Fallecimiento por cualquier causa', porcentaje: 100 },
        { nombre: 'Incapacidad total y permanente', porcentaje: 100 },
        { nombre: 'Auxilio funerario inmediato', valor: 5000000 },
      ],
      origenPerfil: 'Open Finance · Completo',
      desglose: {
        tarifaBase: 42408,
        ajusteRiesgo: 12312,
        ajusteEdad: 7524,
        impuestos: 6156,
      },
    },
    {
      id: 'POL-2026-003918',
      ramo: 'proteccionPagos',
      ramoNombre: 'Protección de Pagos',
      clienteDocumento: '1.032.456.789',
      clienteNombre: 'María Fernanda Ruiz',
      socio: 'Banco Aliado S.A.',
      montoAsegurado: 45000000,
      primaMensual: 28000,
      moneda: 'COP',
      estado: 'pendiente',
      fechaInicio: '2026-08-14T08:00:00',
      fechaVigencia: '2027-08-14T08:00:00',
      idempotencyKey: '9e8a7b6c-1234-4567-89ab-cdef01234567',
      coberturas: [
        { nombre: 'Desempleo involuntario (hasta 6 cuotas)', porcentaje: 100 },
        { nombre: 'Incapacidad médica temporal', porcentaje: 100 },
      ],
      origenPerfil: 'Open Finance · Completo',
      desglose: {
        tarifaBase: 18000,
        ajusteRiesgo: 4500,
        ajusteEdad: 3000,
        impuestos: 2500,
      },
    },
    {
      id: 'POL-2025-001204',
      ramo: 'vidaHipotecario',
      ramoNombre: 'Vida Hipotecario',
      clienteDocumento: '1.032.456.789',
      clienteNombre: 'María Fernanda Ruiz',
      socio: 'Financiera del Norte',
      montoAsegurado: 180000000,
      primaMensual: 72000,
      moneda: 'COP',
      estado: 'rechazada',
      fechaInicio: '2025-11-03T08:00:00',
      fechaVigencia: '2025-11-03T08:00:00',
      motivoRechazo: 'El monto solicitado superó el límite automático para el perfil crediticio en dicha fecha.',
      idempotencyKey: 'fa43bc21-7788-9900-1122-334455667788',
      coberturas: [],
    },
  ],
  siniestros: [
    {
      id: 'SIN-2026-00871',
      polizaId: 'POL-2026-004182',
      clienteDocumento: '1.032.456.789',
      clienteNombre: 'María Fernanda Ruiz',
      tipo: 'Incapacidad temporal por accidente laboral',
      descripcion: 'Accidente en desplazamiento laboral con fractura de clavícula que genera incapacidad médica de 30 días.',
      fechaReporte: '2026-09-11T09:16:00',
      ubicacion: '4.6512, −74.0568 · Cra. 7 # 71-21, Bogotá',
      adjuntos: [
        { nombre: 'Incapacidad_EPS.pdf', tamano: '1.2 MB', tipo: 'doc' },
        { nombre: 'Radiografia_Clinica.jpg', tamano: '640 KB', tipo: 'foto', icono: 'camara' },
      ],
      estado: 'enEvaluacion', // recibido, asignado, enEvaluacion, resuelto
      historial: [
        { estado: 'recibido', fecha: '2026-09-11T09:16:00', detalle: 'Reporte registrado y validado en plataforma.' },
        { estado: 'asignado', fecha: '2026-09-11T11:30:00', detalle: 'Asignado a evaluador médico Dr. Germán Ospina.' },
        { estado: 'enEvaluacion', fecha: '2026-09-12T08:00:00', detalle: 'Dictamen de incapacidad en revisión con historia clínica.' },
      ],
    },
  ],
  colaOfflineSiniestros: [],
  demoConfig: {
    modoDegradadoForzado: false,
    modoRechazoForzado: false,
    modoOfflineSimulado: false,
  },
};

class SolventaDB {
  constructor() {
    this.listeners = [];
    this.channel = null;
    try {
      if (typeof BroadcastChannel !== 'undefined') {
        this.channel = new BroadcastChannel(SOLVENTA_CHANNEL_NAME);
        this.channel.onmessage = (e) => {
          this._notificarListeners(e.data);
        };
      }
    } catch (err) {
      console.warn('BroadcastChannel no soportado, se usará storage event.');
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('storage', (e) => {
        if (e.key === SOLVENTA_STORAGE_KEY) {
          this._notificarListeners({ tipo: 'storage_update' });
        }
      });
    }

    this._asegurarInicializacion();
  }

  _asegurarInicializacion() {
    if (typeof localStorage === 'undefined') return;
    const existente = localStorage.getItem(SOLVENTA_STORAGE_KEY);
    if (!existente) {
      this._guardarRaw(DATOS_SEMILLA);
    }
  }

  _cargarRaw() {
    try {
      const data = localStorage.getItem(SOLVENTA_STORAGE_KEY);
      return data ? JSON.parse(data) : JSON.parse(JSON.stringify(DATOS_SEMILLA));
    } catch (e) {
      console.error('Error al leer localStorage:', e);
      return JSON.parse(JSON.stringify(DATOS_SEMILLA));
    }
  }

  _guardarRaw(data, origenEvento = 'local') {
    try {
      localStorage.setItem(SOLVENTA_STORAGE_KEY, JSON.stringify(data));
      const payload = { tipo: 'cambio_datos', origen: origenEvento, fecha: new Date().toISOString() };
      if (this.channel) {
        this.channel.postMessage(payload);
      }
      this._notificarListeners(payload);
    } catch (e) {
      console.error('Error al guardar en localStorage:', e);
    }
  }

  _notificarListeners(info) {
    for (const fn of this.listeners) {
      try {
        fn(info);
      } catch (e) {
        console.error('Error en listener de DB:', e);
      }
    }
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((f) => f !== listener);
    };
  }

  resetToDefaults() {
    this._guardarRaw(JSON.parse(JSON.stringify(DATOS_SEMILLA)), 'reset');
    return this._cargarRaw();
  }

  // --- Clientes ---
  getCliente() {
    return this._cargarRaw().cliente;
  }

  updateCliente(datos) {
    const raw = this._cargarRaw();
    raw.cliente = { ...raw.cliente, ...datos };
    this._guardarRaw(raw);
    return raw.cliente;
  }

  // --- Pólizas ---
  getPolizas() {
    return this._cargarRaw().polizas;
  }

  getPolizaById(id) {
    return this.getPolizas().find((p) => p.id === id);
  }

  emitirPoliza(nuevaPoliza) {
    const raw = this._cargarRaw();
    // Generación de consecutivo único
    const count = raw.polizas.length + 1;
    const num = String(count + 4182).padStart(6, '0');
    const polizaGenerada = {
      id: nuevaPoliza.id || `POL-2026-${num}`,
      ramo: nuevaPoliza.ramo || 'vidaHipotecario',
      ramoNombre: nuevaPoliza.ramoNombre || 'Vida Hipotecario',
      clienteDocumento: nuevaPoliza.clienteDocumento || raw.cliente.documento,
      clienteNombre: nuevaPoliza.clienteNombre || raw.cliente.nombre,
      socio: nuevaPoliza.socio || 'Banco Aliado S.A.',
      montoAsegurado: nuevaPoliza.montoAsegurado || 250000000,
      primaMensual: nuevaPoliza.primaMensual || 68400,
      moneda: nuevaPoliza.moneda || 'COP',
      estado: nuevaPoliza.estado || 'vigente',
      fechaInicio: nuevaPoliza.fechaInicio || new Date().toISOString(),
      fechaVigencia:
        nuevaPoliza.fechaVigencia ||
        new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
      idempotencyKey: nuevaPoliza.idempotencyKey || `idem-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      coberturas: nuevaPoliza.coberturas || [
        { nombre: 'Fallecimiento por cualquier causa', porcentaje: 100 },
        { nombre: 'Incapacidad total y permanente', porcentaje: 100 },
        { nombre: 'Auxilio funerario inmediato', valor: 5000000 },
      ],
      origenPerfil: nuevaPoliza.origenPerfil || 'Open Finance · Inmediato',
      desglose: nuevaPoliza.desglose || {
        tarifaBase: Math.round((nuevaPoliza.primaMensual || 68400) * 0.62),
        ajusteRiesgo: Math.round((nuevaPoliza.primaMensual || 68400) * 0.18),
        ajusteEdad: Math.round((nuevaPoliza.primaMensual || 68400) * 0.11),
        impuestos: Math.round((nuevaPoliza.primaMensual || 68400) * 0.09),
      },
    };

    raw.polizas.unshift(polizaGenerada);
    this._guardarRaw(raw, 'poliza_emitida');
    return polizaGenerada;
  }

  // --- Siniestros ---
  getSiniestros() {
    return this._cargarRaw().siniestros;
  }

  getSiniestrosPorPoliza(polizaId) {
    return this.getSiniestros().filter((s) => s.polizaId === polizaId);
  }

  getSiniestroById(id) {
    return this.getSiniestros().find((s) => s.id === id);
  }

  radicarSiniestro(datosSiniestro) {
    const raw = this._cargarRaw();
    const count = raw.siniestros.length + 1;
    const num = String(count + 871).padStart(5, '0');
    const radicadoId = `SIN-2026-${num}`;

    const nuevoSiniestro = {
      id: radicadoId,
      polizaId: datosSiniestro.polizaId || (raw.polizas[0] ? raw.polizas[0].id : 'POL-2026-004182'),
      clienteDocumento: datosSiniestro.clienteDocumento || raw.cliente.documento,
      clienteNombre: datosSiniestro.clienteNombre || raw.cliente.nombre,
      tipo: datosSiniestro.tipo || 'Daño material / Accidente',
      descripcion: datosSiniestro.descripcion || 'Reporte de siniestro registrado desde aplicación móvil.',
      fechaReporte: new Date().toISOString(),
      ubicacion: datosSiniestro.ubicacion || '4.6512, −74.0568 · Bogotá, D.C.',
      adjuntos: datosSiniestro.adjuntos || [
        { nombre: 'Foto_Evidencia_1.jpg', tamano: '1.8 MB', tipo: 'foto', icono: 'camara' },
      ],
      estado: 'recibido',
      historial: [
        { estado: 'recibido', fecha: new Date().toISOString(), detalle: 'Siniestro radicado exitosamente en el sistema central.' },
      ],
    };

    raw.siniestros.unshift(nuevoSiniestro);
    this._guardarRaw(raw, 'siniestro_radicado');
    return nuevoSiniestro;
  }

  avanzarEstadoSiniestro(siniestroId) {
    const raw = this._cargarRaw();
    const siniestro = raw.siniestros.find((s) => s.id === siniestroId);
    if (!siniestro) return null;

    const estadosSecuencia = ['recibido', 'asignado', 'enEvaluacion', 'resuelto'];
    const idx = estadosSecuencia.indexOf(siniestro.estado);
    if (idx >= 0 && idx < estadosSecuencia.length - 1) {
      const siguiente = estadosSecuencia[idx + 1];
      siniestro.estado = siguiente;
      const detalleTexto = {
        asignado: 'Asignado al perito de evaluación Dr. Santiago Morales.',
        enEvaluacion: 'Peritaje técnico y médico en curso con soportes adjuntos.',
        resuelto: 'Indemnización aprobada y programada para desembolso.',
      };
      siniestro.historial.push({
        estado: siguiente,
        fecha: new Date().toISOString(),
        detalle: detalleTexto[siguiente] || `Estado cambiado a ${siguiente}`,
      });
      this._guardarRaw(raw, 'siniestro_actualizado');
    }
    return siniestro;
  }

  // --- Cola Offline (Móvil) ---
  getColaOffline() {
    return this._cargarRaw().colaOfflineSiniestros || [];
  }

  encolarSiniestroOffline(datos) {
    const raw = this._cargarRaw();
    const item = {
      idLocal: `OFF-${Date.now()}`,
      datos: datos,
      fechaEncolado: new Date().toISOString(),
      reintentos: 0,
    };
    raw.colaOfflineSiniestros = raw.colaOfflineSiniestros || [];
    raw.colaOfflineSiniestros.push(item);
    this._guardarRaw(raw, 'cola_encolado');
    return item;
  }

  sincronizarColaOffline() {
    const raw = this._cargarRaw();
    const cola = raw.colaOfflineSiniestros || [];
    if (cola.length === 0) return [];

    const radicados = [];
    while (cola.length > 0) {
      const item = cola.shift();
      const count = raw.siniestros.length + 1;
      const num = String(count + 871).padStart(5, '0');
      const radicadoId = `SIN-2026-${num}`;

      const nuevoSiniestro = {
        id: radicadoId,
        polizaId: item.datos.polizaId || (raw.polizas[0] ? raw.polizas[0].id : 'POL-2026-004182'),
        clienteDocumento: item.datos.clienteDocumento || raw.cliente.documento,
        clienteNombre: item.datos.clienteNombre || raw.cliente.nombre,
        tipo: item.datos.tipo || 'Siniestro reportado en modo offline',
        descripcion: item.datos.descripcion || 'Reporte originado sin conexión, sincronizado automáticamente.',
        fechaReporte: item.fechaEncolado,
        fechaSincronizacion: new Date().toISOString(),
        ubicacion: item.datos.ubicacion || '4.6512, −74.0568 · Bogotá, D.C.',
        adjuntos: item.datos.adjuntos || [
          { nombre: 'Foto_Encolada_1.jpg', tamano: '1.8 MB', tipo: 'foto', icono: 'camara' },
        ],
        estado: 'recibido',
        historial: [
          { estado: 'recibido', fecha: new Date().toISOString(), detalle: 'Sincronizado desde la cola offline del dispositivo móvil.' },
        ],
      };
      raw.siniestros.unshift(nuevoSiniestro);
      radicados.push(nuevoSiniestro);
    }

    raw.colaOfflineSiniestros = [];
    this._guardarRaw(raw, 'cola_sincronizada');
    return radicados;
  }

  // --- Configuración de Demostración (PoC) ---
  getDemoConfig() {
    return this._cargarRaw().demoConfig || { ...DATOS_SEMILLA.demoConfig };
  }

  setDemoConfig(clave, valor) {
    const raw = this._cargarRaw();
    raw.demoConfig = raw.demoConfig || { ...DATOS_SEMILLA.demoConfig };
    raw.demoConfig[clave] = valor;
    this._guardarRaw(raw, 'demo_config_cambiada');
    return raw.demoConfig;
  }
}

// Instancia singleton para ser usada directamente
const db = new SolventaDB();
if (typeof window !== 'undefined') {
  window.SolventaDB = db;
}

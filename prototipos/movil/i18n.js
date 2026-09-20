/* ============================================================================
   Solventa · Catálogo bilingüe (ES/EN) y parámetros regionales (Móvil)
   ========================================================================= */

const REGIONES = {
  CO: { etiqueta: 'Colombia', locale: 'es-CO', moneda: 'COP', simbolo: '$', montoBase: 250000000, primaBase: 68400 },
  MX: { etiqueta: 'México',   locale: 'es-MX', moneda: 'MXN', simbolo: '$', montoBase: 1200000,   primaBase: 328 },
  CL: { etiqueta: 'Chile',    locale: 'es-CL', moneda: 'CLP', simbolo: '$', montoBase: 55000000,  primaBase: 15040 },
  PE: { etiqueta: 'Perú',     locale: 'es-PE', moneda: 'PEN', simbolo: 'S/', montoBase: 240000,    primaBase: 66 },
};

const TEXTOS = {
  es: {
    producto: 'Solventa',
    bienvenida: 'Hola, María',
    subtituloBienvenida: 'Billetera digital de seguros',
    tabBilletera: 'Billetera',
    tabSiniestros: 'Siniestros',
    tabPerfil: 'Mi Cuenta',
    idioma: 'Idioma',
    region: 'Región',
    temaOscuro: 'Modo oscuro',
    temaClaro: 'Modo claro',
    
    // M1: Biometría
    accesoBiometrico: 'Acceso Biométrico',
    toqueSensor: 'Toque el sensor para ingresar',
    sensorListo: 'Sensor biométrico activo (Touch ID / Face ID)',
    sensorExito: '¡Identidad biométrica confirmada!',
    usarAlternativo: 'Ingresar con contraseña y código',
    cifradoDispositivo: 'Credenciales protegidas en el enclave seguro del teléfono',
    
    // M2: Alternativo
    accesoAlternativo: 'Acceso Alternativo',
    accesoAltDesc: 'Ingrese con su correo y valide con el código de un solo uso.',
    correo: 'Correo electrónico',
    clave: 'Contraseña',
    codigoOtp: 'Código de seguridad (SMS)',
    reenviarEn: 'Reenviar código en',
    btnEntrar: 'Ingresar',
    btnVolverBiometria: 'Volver al acceso biométrico',
    
    // M3: Billetera
    misPolizas: 'Mis Pólizas Activas',
    sumaAsegurada: 'Suma asegurada',
    vigenteHasta: 'Vigente hasta',
    estadoVigente: 'Vigente',
    estadoPendiente: 'Pendiente',
    carneDigital: 'Carné Digital Solventa',
    tocarGirar: 'Toque la tarjeta para ver coberturas',
    coberturasTitulo: 'Coberturas contratadas',
    reportarSiniestroBtn: 'Reportar un siniestro',
    ultimaSync: 'Última sincronización',
    nuevaPolizaRecibida: 'Póliza recién emitida agregada a la billetera',
    
    // M4: Modo Offline
    modoOfflineTitulo: 'Sin conexión a Internet',
    modoOfflineDesc: 'Está navegando con la copia local cifrada en el dispositivo. Las pólizas siguen disponibles y puede radicar siniestros que se enviarán al recuperar señal.',
    enCache: 'En caché cifrada',
    pendienteSync: 'Siniestros pendientes de sincronizar',
    
    // M5: Reporte de Siniestro
    reportarTitulo: 'Reporte de Siniestro',
    reportarSubtitulo: 'Registro guiado con evidencia y geolocalización',
    paso1Evidencia: '1. Evidencia',
    paso2Detalle: '2. Detalle',
    paso3Confirmar: '3. Envío',
    seleccioneFoto: 'Seleccione una fotografía de evidencia (Demo):',
    foto1: 'Daño puerta lateral (Frontal)',
    foto2: 'Colisión vehicular (Panorámica)',
    foto3: 'Daño estructural vivienda',
    polizaAfectada: 'Póliza afectada',
    ubicacionDetectada: 'Ubicación GPS (Detectada)',
    fechaHoraIncidente: 'Fecha y hora del reporte',
    descripcionHechos: 'Descripción del siniestro',
    descPlaceholder: 'Describa brevemente qué ocurrió y las circunstancias...',
    btnSiguiente: 'Siguiente',
    btnAtras: 'Atrás',
    btnEnviarSiniestro: 'Enviar reclamación',
    
    // M6: Cola Offline
    enColaTitulo: 'Reporte en cola de envío',
    enColaDesc: 'Su reclamación quedó guardada localmente de forma segura. Se enviará sola en cuanto recupere la señal; no necesita repetir el trámite.',
    radicadoProvisional: 'Radicado provisional en cola',
    garantiaIdempotencia: 'Constancia de radicación: Su reclamación se procesará de forma segura y recibirá confirmación en cuanto se recupere la señal.',
    
    // M7: Seguimiento de Siniestro
    radicadoTitulo: 'Reclamación Radicada',
    numRadicado: 'Radicado oficial',
    estadoActual: 'Estado actual',
    sinSiniestros: 'No registra siniestros en este momento.',
    lineaTiempo: 'Línea de tiempo del trámite',
    etapaRecibido: 'Reclamación recibida y validada',
    etapaAsignado: 'Asignada a evaluador perito',
    etapaEvaluacion: 'En peritaje y evaluación técnica',
    etapaResuelto: 'Resolución aprobada e indemnizada',
    verMisSiniestros: 'Ver todos mis siniestros',
    
    // Demo control
    demoTitulo: 'Control de Demostración (PoC)',
    demoDesc: 'Simulación de hardware y escenarios de red',
    switchOffline: 'Simular modo sin conexión (Offline)',
    switchOnline: 'Restaurar conexión (Online)',
    btnSyncCola: 'Sincronizar cola de siniestros ahora',
    btnAvanzarSiniestro: 'Avanzar etapa del siniestro',
    btnResetDatos: 'Restablecer datos demo',
  },
  en: {
    producto: 'Solventa',
    bienvenida: 'Hello, María',
    subtituloBienvenida: 'Digital insurance wallet',
    tabBilletera: 'Wallet',
    tabSiniestros: 'Claims',
    tabPerfil: 'My Account',
    idioma: 'Language',
    region: 'Region',
    temaOscuro: 'Dark mode',
    temaClaro: 'Light mode',
    
    // M1: Biometrics
    accesoBiometrico: 'Biometric Access',
    toqueSensor: 'Touch the sensor to sign in',
    sensorListo: 'Biometric sensor active (Touch ID / Face ID)',
    sensorExito: 'Biometric identity verified!',
    usarAlternativo: 'Sign in with password and code',
    cifradoDispositivo: 'Credentials stored in the device Secure Enclave',
    
    // M2: Alternative
    accesoAlternativo: 'Alternative Sign-in',
    accesoAltDesc: 'Enter your email and one-time verification code.',
    correo: 'E-mail address',
    clave: 'Password',
    codigoOtp: 'Security code (SMS)',
    reenviarEn: 'Resend code in',
    btnEntrar: 'Sign in',
    btnVolverBiometria: 'Return to biometric sign-in',
    
    // M3: Wallet
    misPolizas: 'My Active Policies',
    sumaAsegurada: 'Sum insured',
    vigenteHasta: 'Valid until',
    estadoVigente: 'Active',
    estadoPendiente: 'Pending',
    carneDigital: 'Solventa Digital Card',
    tocarGirar: 'Tap card to flip and view coverages',
    coberturasTitulo: 'Contracted coverages',
    reportarSiniestroBtn: 'File a claim',
    ultimaSync: 'Last synchronized',
    nuevaPolizaRecibida: 'Newly issued policy added to wallet',
    
    // M4: Offline Mode
    modoOfflineTitulo: 'No Internet connection',
    modoOfflineDesc: 'Browsing cached copy encrypted on device. Policies remain accessible and you can file claims that will auto-submit when signal returns.',
    enCache: 'Locally cached',
    pendienteSync: 'Claims queued for sync',
    
    // M5: Claim Filing
    reportarTitulo: 'File an Insurance Claim',
    reportarSubtitulo: 'Guided claim submission with geo-evidence',
    paso1Evidencia: '1. Evidence',
    paso2Detalle: '2. Details',
    paso3Confirmar: '3. Submit',
    seleccioneFoto: 'Select sample evidence photo (Demo):',
    foto1: 'Side door damage (Front view)',
    foto2: 'Vehicle collision (Wide shot)',
    foto3: 'Structural home damage',
    polizaAfectada: 'Affected policy',
    ubicacionDetectada: 'GPS Location (Detected)',
    fechaHoraIncidente: 'Incident timestamp',
    descripcionHechos: 'Description of the incident',
    descPlaceholder: 'Briefly explain what occurred...',
    btnSiguiente: 'Next',
    btnAtras: 'Back',
    btnEnviarSiniestro: 'Submit claim',
    
    // M6: Offline Queue
    enColaTitulo: 'Claim queued for delivery',
    enColaDesc: 'Your claim has been securely saved locally. It will automatically submit once internet is detected; no need to refile.',
    radicadoProvisional: 'Provisional queued ID',
    garantiaIdempotencia: 'Filing confirmation: Your claim is stored securely and will submit automatically once connected.',
    
    // M7: Claim Tracking
    radicadoTitulo: 'Claim Submitted',
    numRadicado: 'Official claim number',
    estadoActual: 'Current status',
    sinSiniestros: 'No claims on record.',
    lineaTiempo: 'Processing timeline',
    etapaRecibido: 'Claim received and validated',
    etapaAsignado: 'Assigned to claims adjuster',
    etapaEvaluacion: 'Under technical assessment',
    etapaResuelto: 'Approved and scheduled for payout',
    verMisSiniestros: 'View all my claims',
    
    // Demo control
    demoTitulo: 'Demo Control (PoC)',
    demoDesc: 'Simulate device hardware and network states',
    switchOffline: 'Simulate Offline mode',
    switchOnline: 'Restore Online connection',
    btnSyncCola: 'Sync queued claims now',
    btnAvanzarSiniestro: 'Advance claim stage',
    btnResetDatos: 'Reset demo data',
  },
};

const t = (clave, idioma = 'es') => TEXTOS[idioma]?.[clave] ?? TEXTOS['es']?.[clave] ?? clave;

const formatoDinero = (valor, reg = 'CO') => {
  const r = REGIONES[reg] || REGIONES.CO;
  return new Intl.NumberFormat(r.locale, {
    style: 'currency',
    currency: r.moneda,
    maximumFractionDigits: 0,
  }).format(valor);
};

const formatoFecha = (iso, reg = 'CO', estilo = 'medium') => {
  const r = REGIONES[reg] || REGIONES.CO;
  try {
    return new Intl.DateTimeFormat(r.locale, {
      dateStyle: estilo,
      timeStyle: 'short',
    }).format(new Date(iso));
  } catch (e) {
    return iso;
  }
};

if (typeof window !== 'undefined') {
  window.REGIONES = REGIONES;
  window.TEXTOS = TEXTOS;
  window.t = t;
  window.formatoDinero = formatoDinero;
  window.formatoFecha = formatoFecha;
}

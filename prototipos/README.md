# Prototipos Ejecutables de Solventa (Validación de Interfaz con Usuario Final)

Este directorio contiene dos prototipos web interactivos e independientes desarrollados específicamente para la **validación de diseño de experiencia de usuario (UX/UI)** con usuarios finales (asesores comerciales, asegurados y clientes de banca en línea):

- **Prototipo Web** (`/prototipos/web/`): Portal para asesores comerciales y analistas de operaciones de Solventa, con pantalla de autenticación simulada, cotización personalizada en vivo, emisión digital y consulta de pólizas.
- **Prototipo Móvil** (`/prototipos/movil/`): Aplicación móvil responsiva (100% nativa sin marcos ficticios de escritorio) para el asegurado, con pantalla de acceso biométrico (Touch ID / Face ID), acceso por SMS, carné digital 3D interactivo y reporte de siniestros.

Ambos prototipos están sincronizados en tiempo real mediante un almacén local reactivo (`localStorage` + `BroadcastChannel`): cualquier póliza emitida en la web aparece de inmediato en la billetera móvil, y cualquier siniestro reportado en el móvil se refleja en la gestión de pólizas web.

---

## Cómo Ejecutar los Prototipos

No se requiere ningún paso de compilación ni instalación de dependencias (`npm`, `webpack`, etc.). Son aplicaciones puras en HTML5, CSS3 y JavaScript moderno.

### Opción 1: Abrir directamente en el navegador
Puedes hacer doble clic o abrir los archivos directamente en tu navegador web:
- **Web**: `prototipos/web/index.html`
- **Móvil**: `prototipos/movil/index.html` *(se recomienda activar el modo responsive de las herramientas de desarrollo de Chrome/Firefox, ej. iPhone 14 o Pixel 7, o abrirlo directamente en el navegador de un celular)*.

### Opción 2: Servir localmente
Desde la raíz del repositorio (`/Users/oscar/code/miso/proyecto-final`):

```bash
# Con Python
python3 -m http.server 8000

# Con Node
npx serve .
```

Luego abre en tu navegador:
- Prototipo Web: [http://localhost:8000/prototipos/web/](http://localhost:8000/prototipos/web/)
- Prototipo Móvil: [http://localhost:8000/prototipos/movil/](http://localhost:8000/prototipos/movil/)

---

## Guía de Interacción y Flujos de Usuario

### 1. Prototipo Web (`/prototipos/web/`)

#### Pantalla de Autenticación con Selección de Tipo de Usuario (W1)
- Al ingresar a la aplicación web, se presenta la pantalla de acceso con diseño dividido 50/50 y selector de perfiles:
- **Panel izquierdo (Marca)**: Gradiente corporativo con el título *"Plataforma de suscripción digital"* y descripción de la propuesta de valor sobre Finanzas Abiertas.
- **Panel derecho (Acceso y Selección de Perfil)**:
  - **Selector de Tipo de Usuario**: Permite elegir interactivamente entre los tres perfiles del sistema:
    1. **Asesora Comercial**: `asesor@solventa.co` · Enfocada en venta asistida, perfilamiento y emisión inmediata (`HU-WEB-01` a `HU-WEB-07`).
    2. **Analista de Operaciones**: `operaciones@solventa.co` · Enfocado en búsqueda multivariable, auditoría 360° y siniestros (`HU-WEB-08` y `HU-WEB-09`).
    3. **Socio de Distribución**: `distribucion@bancoaliado.com` · Banco Aliado B2B, integración API, reintentos y cuotas (`HU-WEB-10` a `HU-WEB-12`).
  - **Aviso para Cliente Asegurado**: Mensaje orientador indicando que los casos de uso del asegurado (`HU-MOV-01` a `HU-MOV-11`) se encuentran disponibles en la aplicación móvil.
  - Al cambiar de rol, las credenciales se actualizan automáticamente y al presionar *"Entrar"* la plataforma discrimina los casos de uso mostrando únicamente las funcionalidades autorizadas para ese perfil.
  - En la cabecera se presenta el nombre, cargo, avatar y chip con el alcance de historias cubiertas, junto a un botón para cambiar de rol o cerrar sesión.

#### Discriminación de Vistas y Casos de Uso por Rol

##### A. Rol: Asesor Comercial (`HU-WEB-01` a `HU-WEB-07`)
- Visualiza de manera exclusiva el módulo **Cotizador y Emisión**:
  1. **Identificación (Paso 1 - HU-WEB-02)**: Captura de datos personales y condiciones del crédito hipotecario con soporte multimoneda y multirregión.
  2. **Consentimiento (Paso 2 - HU-WEB-01)**: Captura de autorización para consulta de Open Finance con verificación SMS simulada.
  3. **Resultado de Cotización (Paso 3 - HU-WEB-03 y HU-WEB-04)**: Tarificación en tiempo real con desglose explicable en pesos (edad, riesgo, impuestos, base) y detección de perfil parcial con indicación de antigüedad.
  4. **Emisión y Cobro (Paso 4 - HU-WEB-05, HU-WEB-06 y HU-WEB-07)**: Formalización con clave de idempotencia, emisión inmediata de número oficial de póliza y explicación clara ante rechazos de suscripción.

##### B. Rol: Analista de Operaciones (`HU-WEB-08` y `HU-WEB-09`)
- Visualiza de manera exclusiva el módulo **Gestión de Pólizas**:
  - **Búsqueda multivariable (HU-WEB-08)**: Filtrado unificado por documento del cliente, número de póliza o socio distribuidor, con filtros de estado (*Vigente*, *Pendiente*, *Rechazada*).
  - **Expediente 360° de la póliza (HU-WEB-09)**: Detalle completo en una sola pantalla con sumas aseguradas, vigencia, coberturas contratadas, estado de pago y siniestros vinculados.

##### C. Rol: Socio de Distribución - Banco Aliado (`HU-WEB-10`, `HU-WEB-11` y `HU-WEB-12`)
- Visualiza de manera exclusiva la **Consola de Socio Distribuidor**:
  - **Cotización Embebida (HU-WEB-10)**: Simulación del portal de banca en línea del socio con oferta integrada de seguro de vida hipotecario.
  - **Credenciales Propias (HU-WEB-10)**: Consola técnica con visualización de cabeceras de autenticación B2B (`Client-Id`).
  - **Garantía de Idempotencia (HU-WEB-11)**: Prueba interactiva de reintento de cotización con clave única, demostrando que la respuesta se entrega sin duplicar registros en base de datos.
  - **Control de Cuotas y Rate Limiting (HU-WEB-12)**: Monitor de consumo y simulador de saturación que reproduce la respuesta `HTTP 429 Too Many Requests` con encabezado `Retry-After: 45s`.

---

### 2. Prototipo Móvil (`/prototipos/movil/`)

#### Pantalla de Autenticación Simulada (M1 y M2)
- Al abrir la aplicación móvil, inicia en la pantalla de bloqueo de seguridad.
- **Acceso Biométrico (M1)**: Tocar el sensor de huella/Touch ID activa una animación de escaneo que desbloquea la billetera digital.
- **Acceso Alternativo (M2)**: Botón para ingresar con correo, contraseña y código SMS demo.
- En la pestaña *"Mi Cuenta"*, el usuario puede pulsar *"Bloquear / Cerrar Sesión"* para regresar a la pantalla de inicio biométrico.

#### Billetera Digital de Pólizas (M3 y M4)
- **Carné Digital 3D**: Al tocar la tarjeta de seguro, esta gira con animación 3D para revelar las coberturas y amparos en el reverso.
- **Sincronización en Vivo**: Cualquier póliza emitida desde el prototipo Web aparece de inmediato en la lista de pólizas del asegurado.
- **Simulación de Conectividad**: Tocar el icono de señal en la barra superior (o en Mi Cuenta) alterna entre conexión activa (4G) y modo sin señal (Offline), permitiendo probar la navegación en caché local.

#### Reporte de Siniestros (M5, M6 y M7)
- **Paso 1 (Evidencia)**: Galería de fotos demostrativas de incidentes (daño en puerta, colisión frontal, daño estructural).
- **Paso 2 (Detalle)**: Selección de la póliza afectada, geolocalización automática de Bogotá y descripción editable de los hechos.
- **Paso 3 (Envío)**:
  - *Con conexión*: Radicación inmediata con código oficial `SIN-2026-XXXXX` y línea de tiempo de seguimiento viva.
  - *Sin conexión*: Guarda el reporte en la cola local segura con constancia de radicación, sincronizándose automáticamente al restablecer la señal.

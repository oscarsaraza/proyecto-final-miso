# Guía de pruebas manuales · Sprint 1

Recorrido para probar a mano, desde cero, HU-MOV-01, HU-MOV-03, HU-MOV-02, HU-MOV-12 y HU-WEB-03 (responsable: Juan Camilo Peña). Los pasos van en orden; cada uno deja el estado que necesita el siguiente.

Requisitos de entorno: README, secciones 2 (backend) y 5 (app móvil y emulador con huella).

## 1. Ramas y PRs

| Historia | Rama | PR | Apunta a |
|---|---|---|---|
| HU-MOV-01 · Huella o rostro | `feature/HU-MOV-01-biometria` | #133 | `main` |
| HU-MOV-03 · Credenciales en Keystore | `feature/HU-MOV-03-keystore` | #134 | #133 |
| HU-MOV-02 · Acceso alternativo | `feature/HU-MOV-02-acceso-alternativo` | #135 | #134 |
| HU-MOV-12 · Cierre de sesión | `feature/HU-MOV-12-cierre-sesion` | #136 | #135 |
| HU-WEB-03 · Desglose de la prima | `feature/HU-WEB-03-desglose-prima` | #137 | `main` |

Los PRs móviles están apilados: cada uno parte del anterior. **La parte móvil se prueba en la rama `feature/HU-MOV-12-cierre-sesion`**, que contiene las cuatro historias. La parte web (pasos 21 a 23) se prueba en `feature/HU-WEB-03-desglose-prima`.

Orden de fusión: #133 → #134 → #135 → #136. #137 es independiente.

## 2. Comandos base (PowerShell)

Todos los comandos son para **PowerShell** (Windows); `<repo>` es la carpeta donde clonaste el repositorio. Un programa de la carpeta actual se llama con `.\` adelante (por ejemplo `.\gradlew`).

Abre tres pestañas de PowerShell:

| Pestaña | Para qué |
|---|---|
| 1 · Backend | Servidor FastAPI; queda ocupada mostrando el log |
| 2 · Emulador | Emulador Android; queda ocupada mostrando el log |
| 3 · Comandos | Gradle, adb y lo demás |

En la pestaña 3, define la ruta de adb una vez por sesión:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
```

Datos de prueba (solo fuera de producción):

| Dato | Valor |
|---|---|
| Correo | `maria.ruiz@correo.co` |
| Contraseña | `Solventa2026!` (13 caracteres) |
| Código SMS | En desarrollo la app lo muestra como "Código de prueba (simula el SMS)" |

Para escribir en un campo del emulador desde la pestaña 3, toca primero el campo y luego ejecuta `& $adb shell input text "maria.ruiz@correo.co"`. Para la contraseña es igual, con `"Solventa2026\!"`; el `!` va escapado porque el shell de Android lo interpreta.

## 3. Recorrido desde cero

### Preparación

**Paso 0 · Estado limpio**

```powershell
# Pestaña 1: backend en la rama móvil
cd <repo>
git switch feature/HU-MOV-12-cierre-sesion
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Si el backend ya estaba corriendo, deténlo con `Ctrl+C` y lánzalo de nuevo: los códigos, intentos y bloqueos viven en memoria y así quedan en cero.

Si no existe `backend\.venv`, créalo una vez (o usa Poetry, README sección 2.2): `python -m venv .venv` y luego `.\.venv\Scripts\python -m pip install -r requirements.txt`.

```powershell
# Pestaña 2: emulador
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd solventa
```

```powershell
# Pestaña 3: esperar a que Android termine de arrancar (debe imprimir 1)
& $adb shell getprop sys.boot_completed

# Quitar la app y la huella de pruebas anteriores
& $adb uninstall com.solventa.app
& $adb shell locksettings clear --old 1234
```

**Esperado:** el backend muestra `Uvicorn running on http://0.0.0.0:8000`, el emulador está en su pantalla de inicio, `getprop` imprime `1` y el emulador no tiene app Solventa ni bloqueo de pantalla.

**Paso 1 · Pruebas automatizadas del backend**

```powershell
cd <repo>\backend
.\.venv\Scripts\python -m pytest
```

**Esperado:** `39 passed, 5 skipped` y cobertura total cercana al 97 %. Las 5 omitidas son pruebas TDD de historias de otros integrantes.

**Paso 2 · Pruebas automatizadas del móvil**

```powershell
cd <repo>\movil
.\gradlew testDebugUnitTest
```

**Esperado:** `BUILD SUCCESSFUL`. El reporte queda en `movil\app\build\reports\tests\testDebugUnitTest\index.html` con 48 pruebas en 4 clases y 0 fallos.

**Paso 3 · Instalar la app**

```powershell
.\gradlew installDebug
& $adb shell am start -n com.solventa.app/.MainActivity
```

**Esperado:** `Installed on 1 device.` y la app abierta en el emulador. Si falla con `NullPointerException ... freeStorage`, el emulador no había terminado de arrancar: repite cuando `getprop sys.boot_completed` devuelva `1`.

### Backend por Swagger (HU-MOV-02 y HU-MOV-12)

Abre http://localhost:8000/docs.

**Paso 4 · Código de un solo uso** · caso 02.1 · tarea #123

1. `POST /api/v1/auth/otp` con `{"email": "maria.ruiz@correo.co"}`.
2. Repite con `{"email": "nadie@correo.co"}`.

**Esperado:** 200 con `debug_code` de 6 dígitos para María, y 200 con `debug_code: null` para el correo desconocido (no revela qué correos existen).

**Paso 5 · Login, logout y revocación** · casos 02.2, 12.1 y 12.2 · tareas #123 y #127

1. Pide un código para María (`/auth/otp`).
2. `POST /api/v1/auth/login` con correo, contraseña y ese código → 200. Copia el `refresh_token`.
3. `POST /api/v1/auth/refresh` con ese token → 200 con tokens nuevos. Copia el nuevo `refresh_token`.
4. `POST /api/v1/auth/refresh` otra vez con el token **viejo** → 401 (cada refresh token se usa una sola vez).
5. `POST /api/v1/auth/logout` con el token **nuevo** → 204.
6. `POST /api/v1/auth/refresh` con ese mismo token → 401 (quedó revocado).

**Paso 6 · Bloqueo por intentos** · caso 02.3 · tarea #123

1. Pide un código para María.
2. Envía `/auth/login` tres veces con la contraseña `mala` y ese código.

**Esperado:** 401, 401 y 423 ("Cuenta bloqueada por intentos fallidos hasta …").

Al terminar, **reinicia el backend** (`Ctrl+C` y vuelve a lanzarlo) para quitar el bloqueo.

### App sin huella registrada (HU-MOV-01 y HU-MOV-02)

**Paso 7 · Pantalla biométrica sin huella** · casos 01.1 y 01.5 · tareas #116 y #117

Con la app abierta (paso 3).

**Esperado:**
- Título "Acceso biométrico" y botón "Ingresar con contraseña y código".
- Mensaje en rojo "No hay huella ni rostro registrados en este teléfono…".
- El círculo del sensor está deshabilitado y no responde al tocarlo.

**Paso 8 · Errores del acceso alternativo** · casos 02.4, 02.8 y 02.7 · tareas #124, #125 y #126

1. Toca "Ingresar con contraseña y código".
2. Correo `maria.ruiz@correo.co` → **Enviar código**. Aparece "Código de prueba (simula el SMS): ######".
3. Escribe la contraseña `mala` y el código → **Ingresar**. Sale "Correo, contraseña o código incorrectos. Al tercer intento fallido la cuenta se bloquea 15 minutos."
4. Detén el backend (`Ctrl+C` en la pestaña 1) y vuelve a tocar **Ingresar**. Sale "No fue posible conectar con Solventa…".
5. Lanza de nuevo el backend.

**Paso 9 · Bloqueo desde la app** · caso 02.9 · tarea #126

1. Pide un código nuevo (**Reenviar**).
2. Toca **Ingresar** tres veces con la contraseña `mala`.

**Esperado:** a la tercera, "Cuenta bloqueada por 15 minutos tras 3 intentos fallidos." y el botón **Ingresar** deshabilitado.

Al terminar, **reinicia el backend** y la app: `& $adb shell am force-stop com.solventa.app` y luego `& $adb shell am start -n com.solventa.app/.MainActivity`.

**Paso 10 · Login sin biometría y cierre de sesión** · casos 12.3, 12.4 y 12.7 · tareas #125 y #128

1. Entra con el correo, la contraseña correcta y un código nuevo.
2. Como no hay huella, entras directo a "Hola, María Ruiz", sin ofrecer biometría.
3. Toca **Cerrar sesión** → **Cancelar**. Sigues en "Hola, María Ruiz".
4. Toca **Cerrar sesión** → **Cerrar sesión**.

**Esperado:** vuelve a la bienvenida con "Cerró sesión en este teléfono…", y en la pestaña 1 aparece `POST /api/v1/auth/logout HTTP/1.1" 204`.

### Registrar huella en el emulador

**Paso 11 · Huella del emulador** (preparación, no es un caso)

1. Abre el registro de huella desde la pestaña 3:
   ```powershell
   & $adb shell am start -a android.settings.BIOMETRIC_ENROLL
   ```
2. Elige **"PIN • Fingerprint • Face"**, escribe `1234`, **Next**, repite `1234` y **Confirm**.
3. Acepta las pantallas de huella hasta "Touch the sensor".
4. Ejecuta `& $adb -e emu finger touch 1` varias veces, hasta que diga "Fingerprint added", y toca **Done**.
5. Si después aparece una **pantalla en blanco** (registro de rostro, que el emulador no soporta), ciérrala:
   ```powershell
   & $adb shell am force-stop com.android.settings
   ```

Verificación: `& $adb shell dumpsys fingerprint` debe mostrar `"count":1`.

### App con huella (HU-MOV-01, HU-MOV-02 y HU-MOV-03)

Abre la app: `& $adb shell am start -n com.solventa.app/.MainActivity`.

**Paso 12 · Sin sesión guardada**

**Esperado:** el sensor sigue deshabilitado, con "Cerró sesión…" o "Para activar el acceso biométrico, ingrese primero con contraseña y código." Todavía no hay sesión cifrada que la huella pueda abrir.

**Paso 13 · Rechazar la biometría** · caso 02.6 · tarea #125

1. Entra con contraseña y código.
2. Aparece "¿Activar ingreso con huella o rostro?". Toca **Ahora no**.
3. Entras a "Hola, María Ruiz".
4. Cierra la app (`& $adb shell am force-stop com.solventa.app`) y ábrela de nuevo.

**Esperado:** no abre con huella; sigue pidiendo contraseña y código, porque no se guardó la sesión.

**Paso 14 · Activar la biometría** · casos 02.5 y 03.1 · tareas #119 y #125

1. Entra con contraseña y código.
2. En "¿Activar ingreso con huella o rostro?", toca **Activar**.
3. Sale el diálogo del sistema. Ejecuta `& $adb -e emu finger touch 1`.

**Esperado:** entras a "Hola, María Ruiz". El sistema pidió huella para cifrar la sesión.

**Paso 15 · La sesión quedó cifrada** · caso 03.2 · tarea #120

```powershell
& $adb shell run-as com.solventa.app cat shared_prefs/solventa_session.xml
```

**Esperado:** solo `ciphertext` e `iv` en Base64. Ningún texto con forma de token (`eyJ...`).

**Paso 16 · Entrar con huella** · casos 01.2 y 03.3 · tareas #117 y #121

1. Cierra la app (`force-stop`) y ábrela.
2. El diálogo de huella se abre solo. Ejecuta `& $adb -e emu finger touch 1`.

**Esperado:** entras directo a "Hola, María Ruiz", sin contraseña.

**Paso 17 · Variantes del diálogo** · casos 01.3, 01.6 y 01.7 · tareas #117 y #118

Para cada variante, cierra y abre la app para que salga el diálogo:

1. `& $adb -e emu finger touch 2` (huella no registrada) → el diálogo dice "Not recognized" y sigue abierto. Luego `finger touch 1` para entrar.
2. Botón atrás ◁ en el diálogo → "Autenticación cancelada…". Al tocar el sensor, el diálogo vuelve a abrirse.
3. Botón **"Usar contraseña"** del diálogo → abre el acceso alternativo. Vuelve con "Volver al acceso biométrico".

**Paso 18 · Bloqueo del sensor** · caso 01.4 · tarea #117

1. Con el diálogo abierto, ejecuta `& $adb -e emu finger touch 2` cinco veces.

**Esperado:** "Demasiados intentos fallidos. Ingrese con contraseña y código." El bloqueo del sensor dura unos 30 segundos.

**Paso 19 · Cierre de sesión con biometría activa** · casos 12.4 y 12.5 · tarea #128

1. Entra con huella, toca **Cerrar sesión** y confirma.
2. Toca el sensor.

**Esperado:** el sensor no abre la sesión y pide contraseña y código. El comando del paso 15 ahora muestra `<map />`, vacío.

**Paso 20 · Una huella nueva invalida la llave** · caso 03.4 · tarea #121

1. Entra con contraseña y código y activa la biometría (como en el paso 14).
2. Agrega una segunda huella: `& $adb shell am start -a android.settings.BIOMETRIC_ENROLL`, PIN `1234`, y `& $adb -e emu finger touch 2` hasta "Fingerprint added".
3. Cierra la app y ábrela.

**Esperado:** "Por seguridad, la sesión guardada se reinició. Ingrese con contraseña y código."

### Web y motor de tarifa (HU-WEB-03)

Detén el backend (`Ctrl+C`) y cambia de rama:

```powershell
cd <repo>
git switch feature/HU-WEB-03-desglose-prima
cd backend
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`pytest` debe dar `34 passed, 4 skipped`.

**Paso 21 · Cotización con desglose** · casos 3.1 y 3.2 · tarea #130

En Swagger, `POST /api/v1/experience/quotes` con:

```json
{"document_type": "CC", "document_number": "1020304050", "birth_date": "1990-05-15", "insured_amount": 100000000, "occupation_risk": 2}
```

**Esperado:** 200 con los planes `basic`, `standard` y `premium`. En cada uno, la suma de los `amount` del `breakdown` es igual a `monthly_premium`.

**Paso 22 · Factores que suben y bajan** · casos 3.3 y 3.4 · tarea #130

1. Repite con `"birth_date": "1970-01-01"` y `"occupation_risk": 4`. Los factores `age` y `occupation` salen positivos, y el plan `basic` tiene `plan` negativo.
2. `POST /api/v1/quote-edge/quotes` con el mismo cuerpo: sin la cabecera `X-Partner-Id` da 401, y con ella da 200.

**Paso 23 · Pruebas del componente web** · casos 3.5 a 3.7 · tareas #131 y #132

Si Windows bloquea los binarios nativos de Angular (Control de aplicaciones inteligente), las pruebas web se revisan en el CI: en el PR #137, el job **Web CI (Angular 22 & Vitest)** debe estar en verde con 25 pruebas. Fuera de ese caso basta con `npm ci` y `npm test -- --watch=false`; con Docker también se pueden correr así:

```powershell
cd <repo>\web
docker run --rm -v "${PWD}:/app" -v solventa_web_modules:/app/node_modules -w /app node:22 sh -c "npm ci && npm test -- --watch=false"
```

El desglose se ve en la pantalla del cotizador cuando HU-WEB-02 (Oscar) cargue la cotización.

Al terminar, vuelve a la rama móvil: `git switch feature/HU-MOV-12-cierre-sesion`.

## 4. Mapa de casos por tarea

| Tarea | Casos | Pasos |
|---|---|---|
| #116 Pantalla biométrica | 01.1 | 7 |
| #117 BiometricPrompt | 01.2, 01.3, 01.4, 01.5 | 7, 16, 17, 18 |
| #118 AuthViewModel biométrico | 01.6, 01.7 | 17 |
| #119 Llave Keystore | 03.1 | 14 |
| #120 Repositorio cifrado | 03.2 | 15 |
| #121 Desbloqueo con CryptoObject | 03.3, 03.4 | 16, 20 |
| #122 Pruebas TC-S1-11 | — | 2 |
| #123 Backend login | 02.1, 02.2, 02.3 | 4, 5, 6 |
| #124 Pantalla alternativa | 02.4 | 8 |
| #125 Cliente HTTP | 02.5, 02.6, 02.7 | 8, 10, 13, 14 |
| #126 Bloqueo por intentos | 02.8, 02.9 | 8, 9 |
| #127 Backend logout | 12.1, 12.2 | 5 |
| #128 Cierre de sesión en la app | 12.3, 12.4, 12.5, 12.7 (12.6 sin red: solo automatizada) | 10, 19 |
| #129 Pruebas TC-S1-12 | — | 1, 2 |
| #130 Motor de tarifa | 3.1 a 3.4 | 21, 22 |
| #131 Componente de desglose | 3.5, 3.6 | 23 |
| #132 Pruebas Vitest | 3.7 | 23 |

## 5. Resumen de pruebas automatizadas

| Suite | Comando | Última corrida |
|---|---|---|
| Backend, rama HU-MOV-12 | `.\.venv\Scripts\python -m pytest` | 39 aprobadas, 5 omitidas, 97 % de cobertura |
| Backend, rama HU-WEB-03 | `.\.venv\Scripts\python -m pytest` | 34 aprobadas, 4 omitidas, 94 % de cobertura |
| Móvil, rama HU-MOV-12 | `.\gradlew testDebugUnitTest` | 48 aprobadas |
| Web, rama HU-WEB-03 | CI `Web CI (Angular 22 & Vitest)` | 25 aprobadas en 6 archivos, y el build de producción en verde |

Los cinco PRs (#133 a #137) pasan los cuatro jobs del CI: backend, web, móvil y Terraform.

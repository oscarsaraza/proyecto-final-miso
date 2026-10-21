package com.solventa.app.ui.auth

import com.solventa.app.data.session.BoundAccount
import com.solventa.app.data.session.FakeSessionCrypto
import com.solventa.app.data.session.InMemorySessionStore
import com.solventa.app.data.session.SecureSessionRepository
import com.solventa.app.domain.auth.AuthApi
import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult
import com.solventa.app.domain.auth.DeviceCredential
import com.solventa.app.domain.auth.LoginResult
import com.solventa.app.domain.auth.OtpResult
import com.solventa.app.domain.auth.ResetResult
import com.solventa.app.domain.auth.SessionTokens
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.TestDispatcher
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import javax.crypto.Cipher

@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {

    private val credential = DeviceCredential("device-123", "secreto")
    private val newTokens = SessionTokens("new.access.jwt", "new-refresh")
    private val registeredCredential = DeviceCredential("device-nuevo", "secreto-nuevo")

    private lateinit var dispatcher: TestDispatcher
    private lateinit var crypto: FakeSessionCrypto
    private lateinit var store: InMemorySessionStore
    private lateinit var repository: SecureSessionRepository
    private lateinit var authApi: FakeAuthApi
    private lateinit var viewModel: AuthViewModel

    @Before
    fun setUp() {
        dispatcher = UnconfinedTestDispatcher()
        Dispatchers.setMain(dispatcher)
        crypto = FakeSessionCrypto()
        store = InMemorySessionStore()
        repository = SecureSessionRepository(crypto, store)
        repository.save(credential, repository.encryptionCipher(), EMAIL, "María Ruiz")
        authApi = FakeAuthApi()
        viewModel = AuthViewModel(repository, authApi)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun advanceSeconds(seconds: Int) {
        dispatcher.scheduler.advanceTimeBy(seconds * 1_000L)
        dispatcher.scheduler.runCurrent()
    }

    private fun withoutBoundAccounts() {
        store.clear()
        viewModel = AuthViewModel(repository, authApi)
    }

    @Test
    fun `debe inicializar el estado con la cuenta de la huella elegida`() {
        val state = viewModel.uiState.value
        assertFalse(state.isAuthenticated)
        assertFalse(state.isLocked)
        assertEquals(AuthStatus.IDLE, state.status)
        assertFalse(state.showAlternativeAccess)
        assertEquals(listOf(BoundAccount(EMAIL, "María Ruiz")), state.biometricAccounts)
        assertEquals(EMAIL, state.selectedAccountEmail)
    }

    // TC-S1-09: ingreso con huella (HU-MOV-01)

    @Test
    fun `TC-S1-09 huella correcta entra con la credencial de la cuenta elegida`() {
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        val state = viewModel.uiState.value
        assertTrue(state.isAuthenticated)
        assertEquals(AuthStatus.AUTHENTICATED, state.status)
        assertEquals(credential, authApi.lastBiometricCredential)
        assertEquals(newTokens, repository.activeSession)
        assertEquals(EMAIL, state.currentAccountEmail)
        assertTrue(state.biometricEnabled)
        assertEquals(1, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 muestra estado de verificacion mientras el dialogo esta abierto`() {
        val pending = CompletableDeferred<BiometricResult>()
        val authenticator = FakeBiometricAuthenticator(deferred = pending)

        viewModel.authenticateWithBiometrics(authenticator)
        assertEquals(AuthStatus.AUTHENTICATING, viewModel.uiState.value.status)

        pending.complete(BiometricResult.Success(checkNotNull(authenticator.lastCipher)))
        assertTrue(viewModel.uiState.value.isAuthenticated)
    }

    @Test
    fun `TC-S1-09 no abre un segundo dialogo si ya hay uno en curso`() {
        val authenticator = FakeBiometricAuthenticator(deferred = CompletableDeferred())

        viewModel.authenticateWithBiometrics(authenticator)
        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(1, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 cancelar el dialogo deja la sesion cerrada y permite reintentar`() {
        val authenticator = FakeBiometricAuthenticator(result = BiometricResult.Cancelled)

        viewModel.authenticateWithBiometrics(authenticator)
        assertEquals(AuthStatus.CANCELLED, viewModel.uiState.value.status)
        assertNull(repository.activeSession)

        viewModel.authenticateWithBiometrics(authenticator)
        assertEquals(2, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 boton de contrasena del dialogo lleva al acceso alternativo con el correo de la cuenta`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.UseAlternative))

        assertTrue(viewModel.uiState.value.showAlternativeAccess)
        assertEquals(EMAIL, viewModel.uiState.value.prefillEmail)
    }

    @Test
    fun `TC-S1-09 sin huellas registradas en el telefono no abre el dialogo`() {
        val authenticator = FakeBiometricAuthenticator(availability = BiometricAvailability.NOT_ENROLLED)

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.BIOMETRIC_NOT_ENROLLED, viewModel.uiState.value.status)
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 sin sensor no abre el dialogo`() {
        val authenticator = FakeBiometricAuthenticator(availability = BiometricAvailability.UNAVAILABLE)

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.BIOMETRIC_UNAVAILABLE, viewModel.uiState.value.status)
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 bloqueo del sensor lleva al ingreso con contrasena y codigo`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.LockedOut))

        assertEquals(AuthStatus.BIOMETRIC_LOCKED_OUT, viewModel.uiState.value.status)
        assertTrue(viewModel.uiState.value.showAlternativeAccess)
        assertFalse(viewModel.uiState.value.isAuthenticated)
    }

    @Test
    fun `TC-S1-09 error del sensor lleva al ingreso con contrasena y codigo`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.Error(code = 99)))

        assertEquals(AuthStatus.BIOMETRIC_ERROR, viewModel.uiState.value.status)
        assertTrue(viewModel.uiState.value.showAlternativeAccess)
    }

    @Test
    fun `TC-S1-09 huella desactivada en el servidor desvincula solo esa cuenta`() {
        authApi.biometricResult = LoginResult.InvalidCredentials

        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        assertEquals(AuthStatus.SESSION_RESET, viewModel.uiState.value.status)
        assertFalse(repository.isBound(EMAIL))
        assertTrue(viewModel.uiState.value.biometricAccounts.isEmpty())
    }

    @Test
    fun `TC-S1-09 sin conexion la huella no entra pero conserva el vinculo`() {
        authApi.biometricResult = LoginResult.NetworkError

        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        assertEquals(AuthStatus.SERVER_UNREACHABLE, viewModel.uiState.value.status)
        assertTrue(repository.isBound(EMAIL))
    }

    @Test
    fun `TC-S1-09 ingreso suspendido tambien detiene la huella hasta que pase el tiempo`() {
        authApi.biometricResult = LoginResult.Locked(retryAfterSeconds = 3)

        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())
        assertEquals(AuthStatus.ACCOUNT_LOCKED, viewModel.uiState.value.status)

        advanceSeconds(3)
        assertEquals(AuthStatus.IDLE, viewModel.uiState.value.status)
        assertFalse(viewModel.uiState.value.isLocked)
    }

    @Test
    fun `TC-S1-09 cambiar de usuario abre el ingreso con el correo vacio`() {
        viewModel.switchUser()

        assertTrue(viewModel.uiState.value.showAlternativeAccess)
        assertNull(viewModel.uiState.value.prefillEmail)
        assertTrue(repository.isBound(EMAIL))
    }

    @Test
    fun `TC-S1-09 ingresar con contrasena precarga el correo de la cuenta elegida`() {
        viewModel.onAlternativeAccessSelected()

        assertEquals(EMAIL, viewModel.uiState.value.prefillEmail)
    }

    // TC-S1-11: credencial custodiada en el Keystore (HU-MOV-03)

    @Test
    fun `TC-S1-11 sin huella vinculada pide ingresar primero con contrasena`() {
        withoutBoundAccounts()
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.NO_STORED_SESSION, viewModel.uiState.value.status)
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-11 llave invalidada reinicia el vinculo sin abrir el dialogo`() {
        crypto.invalidated = true
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.SESSION_RESET, viewModel.uiState.value.status)
        assertFalse(repository.hasStoredSession())
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-11 credencial alterada se descarta y no autentica`() {
        val stored = store.sessions.single()
        stored.ciphertext[0] = (stored.ciphertext[0].toInt() xor 0x01).toByte()

        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        assertEquals(AuthStatus.SESSION_RESET, viewModel.uiState.value.status)
        assertFalse(viewModel.uiState.value.isAuthenticated)
        assertFalse(repository.hasStoredSession())
        assertNull(authApi.lastBiometricCredential)
    }

    @Test
    fun `volver desde el acceso alternativo restablece la pantalla de huella`() {
        viewModel.onAlternativeAccessSelected()

        viewModel.onBackToBiometrics()

        assertFalse(viewModel.uiState.value.showAlternativeAccess)
        assertEquals(AuthStatus.IDLE, viewModel.uiState.value.status)
    }

    // Varias cuentas con huella en el mismo teléfono

    @Test
    fun `otra cuenta activa su huella sin quitar la de la primera`() {
        authApi.loginResult = LoginResult.Success(newTokens, "Pedro Gómez")
        val authenticator = FakeBiometricAuthenticator()

        viewModel.switchUser()
        viewModel.authenticateWithPassword(PEDRO, PASSWORD, OTP, authenticator)
        assertTrue(viewModel.uiState.value.offerBiometricEnrollment)
        viewModel.enableBiometricUnlock(authenticator)

        val state = viewModel.uiState.value
        assertEquals(
            listOf(BoundAccount(EMAIL, "María Ruiz"), BoundAccount(PEDRO, "Pedro Gómez")),
            state.biometricAccounts,
        )
        assertEquals(PEDRO, state.selectedAccountEmail)
        assertTrue(repository.isBound(EMAIL))
    }

    @Test
    fun `elegir otra cuenta entra con la huella de esa cuenta`() {
        val pedroCredential = DeviceCredential("device-pedro", "secreto-pedro")
        repository.save(pedroCredential, repository.encryptionCipher(), PEDRO, "Pedro Gómez")
        viewModel = AuthViewModel(repository, authApi)
        assertEquals(PEDRO, viewModel.uiState.value.selectedAccountEmail)

        viewModel.selectAccount(EMAIL)
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        assertEquals(credential, authApi.lastBiometricCredential)
        assertEquals(EMAIL, viewModel.uiState.value.currentAccountEmail)
    }

    @Test
    fun `cerrar sesion deja elegida la cuenta que estaba adentro`() {
        repository.save(DeviceCredential("device-pedro", "s"), repository.encryptionCipher(), PEDRO, "Pedro Gómez")
        viewModel = AuthViewModel(repository, authApi)
        viewModel.selectAccount(EMAIL)
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        viewModel.requestLogout()
        viewModel.confirmLogout()

        assertEquals(EMAIL, viewModel.uiState.value.selectedAccountEmail)
        assertEquals(2, viewModel.uiState.value.biometricAccounts.size)
    }

    @Test
    fun `desactivar la huella de una cuenta conserva la de la otra`() {
        repository.save(DeviceCredential("device-pedro", "s"), repository.encryptionCipher(), PEDRO, "Pedro Gómez")
        viewModel = AuthViewModel(repository, authApi)
        authApi.biometricResult = LoginResult.Success(newTokens, "Pedro Gómez")
        viewModel.selectAccount(PEDRO)
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        viewModel.disableBiometrics()
        viewModel.requestLogout()
        viewModel.confirmLogout()

        assertEquals(listOf(BoundAccount(EMAIL, "María Ruiz")), viewModel.uiState.value.biometricAccounts)
        assertEquals(EMAIL, viewModel.uiState.value.selectedAccountEmail)
        assertEquals("device-pedro", authApi.lastRevokedDevice)
    }

    // TC-S1-10: acceso alternativo con contraseña y código por SMS (HU-MOV-02)

    @Test
    fun `TC-S1-10 solicitar codigo marca el envio y expone el codigo de prueba`() {
        authApi.otpResult = OtpResult.Sent(debugCode = "417902")

        viewModel.requestOtp(" maria.ruiz@correo.co ")

        val form = viewModel.uiState.value.alternativeLogin
        assertTrue(form.otpSent)
        assertEquals("417902", form.debugOtpCode)
        assertEquals("maria.ruiz@correo.co", authApi.lastOtpEmail)
    }

    @Test
    fun `TC-S1-10 reenviar el codigo exige esperar 60 segundos`() {
        viewModel.requestOtp(EMAIL)
        assertEquals(60, viewModel.uiState.value.otpCooldownSeconds)

        viewModel.requestOtp(EMAIL)
        assertEquals(1, authApi.otpCount)

        advanceSeconds(60)
        assertEquals(0, viewModel.uiState.value.otpCooldownSeconds)
        viewModel.requestOtp(EMAIL)
        assertEquals(2, authApi.otpCount)
    }

    @Test
    fun `TC-S1-10 la espera para reenviar es por correo`() {
        viewModel.requestOtp(EMAIL)

        assertFalse(viewModel.uiState.value.canRequestOtp(" MARIA.RUIZ@correo.co "))
        assertTrue(viewModel.uiState.value.canRequestOtp(PEDRO))
        viewModel.requestOtp(PEDRO)
        assertEquals(2, authApi.otpCount)
    }

    @Test
    fun `TC-S1-10 ingresar reinicia la espera para pedir codigo`() {
        viewModel.requestOtp(EMAIL)

        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        assertEquals(0, viewModel.uiState.value.otpCooldownSeconds)
        assertTrue(viewModel.uiState.value.canRequestOtp(EMAIL))
    }

    @Test
    fun `TC-S1-10 servidor pide esperar antes de otro codigo`() {
        authApi.otpResult = OtpResult.TooManyRequests(retryAfterSeconds = 25)

        viewModel.requestOtp(EMAIL)

        assertEquals(AlternativeLoginError.TOO_MANY_REQUESTS, viewModel.uiState.value.alternativeLogin.error)
        assertEquals(25, viewModel.uiState.value.otpCooldownSeconds)
    }

    @Test
    fun `TC-S1-10 fallo del envio del SMS se informa`() {
        authApi.otpResult = OtpResult.SendFailed

        viewModel.requestOtp(EMAIL)

        assertEquals(AlternativeLoginError.SMS_UNAVAILABLE, viewModel.uiState.value.alternativeLogin.error)
        assertEquals(0, viewModel.uiState.value.otpCooldownSeconds)
    }

    @Test
    fun `TC-S1-10 fallo al solicitar codigo muestra error de conexion`() {
        authApi.otpResult = OtpResult.Failed

        viewModel.requestOtp(EMAIL)

        assertEquals(AlternativeLoginError.NETWORK, viewModel.uiState.value.alternativeLogin.error)
    }

    @Test
    fun `TC-S1-10 login correcto de una cuenta sin huella ofrece activarla`() {
        withoutBoundAccounts()

        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        val state = viewModel.uiState.value
        assertTrue(state.offerBiometricEnrollment)
        assertFalse(state.isAuthenticated)
        assertEquals("María Ruiz", state.fullName)
        assertEquals(newTokens, repository.activeSession)
    }

    @Test
    fun `TC-S1-10 login correcto de una cuenta con huella entra sin volver a ofrecerla`() {
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertFalse(viewModel.uiState.value.offerBiometricEnrollment)
        assertTrue(viewModel.uiState.value.biometricEnabled)
    }

    @Test
    fun `TC-S1-10 login correcto sin biometria entra directo`() {
        withoutBoundAccounts()

        viewModel.authenticateWithPassword(
            EMAIL,
            PASSWORD,
            OTP,
            FakeBiometricAuthenticator(availability = BiometricAvailability.NOT_ENROLLED),
        )

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertFalse(viewModel.uiState.value.offerBiometricEnrollment)
    }

    @Test
    fun `TC-S1-10 activar la huella vincula el telefono a la cuenta y guarda su credencial cifrada`() {
        withoutBoundAccounts()
        val authenticator = FakeBiometricAuthenticator()
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, authenticator)

        viewModel.enableBiometricUnlock(authenticator)

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertTrue(viewModel.uiState.value.biometricEnabled)
        assertEquals(newTokens.accessToken, authApi.lastRegisterToken)
        val reopened = SecureSessionRepository(crypto, store)
        assertEquals(registeredCredential, reopened.unlock(EMAIL, checkNotNull(reopened.decryptionCipher(EMAIL))))
    }

    @Test
    fun `TC-S1-10 cancelar la huella al activarla revoca el telefono en el servidor`() {
        withoutBoundAccounts()
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        viewModel.enableBiometricUnlock(FakeBiometricAuthenticator(result = BiometricResult.Cancelled))

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertFalse(viewModel.uiState.value.biometricEnabled)
        assertFalse(repository.hasStoredSession())
        assertEquals(registeredCredential.deviceId, authApi.lastRevokedDevice)
    }

    @Test
    fun `TC-S1-10 rechazar la huella entra sin vincular el telefono`() {
        withoutBoundAccounts()
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        viewModel.skipBiometricEnrollment()

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertFalse(repository.hasStoredSession())
        assertNull(authApi.lastRegisterToken)
    }

    @Test
    fun `TC-S1-10 credenciales incorrectas cuentan los intentos fallidos`() {
        authApi.loginResult = LoginResult.InvalidCredentials

        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())
        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())

        val state = viewModel.uiState.value
        assertEquals(2, state.failedAttempts)
        assertEquals(AlternativeLoginError.INVALID_CREDENTIALS, state.alternativeLogin.error)
        assertFalse(state.isAuthenticated)
    }

    @Test
    fun `TC-S1-10 formato invalido no cuenta como intento fallido`() {
        authApi.loginResult = LoginResult.InvalidFormat

        viewModel.authenticateWithPassword(EMAIL, PASSWORD, "12", FakeBiometricAuthenticator())

        assertEquals(AlternativeLoginError.INVALID_FORMAT, viewModel.uiState.value.alternativeLogin.error)
        assertEquals(0, viewModel.uiState.value.failedAttempts)
    }

    @Test
    fun `TC-S1-10 ingreso suspendido impide nuevos intentos mientras dura`() {
        authApi.loginResult = LoginResult.Locked(retryAfterSeconds = 900)

        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        assertTrue(viewModel.uiState.value.isLocked)
        assertEquals(900, viewModel.uiState.value.lockedSeconds)
        assertEquals(AlternativeLoginError.ACCOUNT_LOCKED, viewModel.uiState.value.alternativeLogin.error)
        assertEquals(1, authApi.loginCount)
    }

    @Test
    fun `TC-S1-10 la suspension se levanta sola al cumplirse el tiempo sin cerrar la app`() {
        authApi.loginResult = LoginResult.Locked(retryAfterSeconds = 900)
        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())

        advanceSeconds(899)
        assertEquals(1, viewModel.uiState.value.lockedSeconds)

        advanceSeconds(1)
        assertFalse(viewModel.uiState.value.isLocked)
        assertNull(viewModel.uiState.value.alternativeLogin.error)

        authApi.loginResult = LoginResult.Success(newTokens, "María Ruiz")
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())
        assertEquals(2, authApi.loginCount)
        assertTrue(viewModel.uiState.value.isAuthenticated)
    }

    @Test
    fun `TC-S1-10 limite por IP espera el tiempo que indica el servidor`() {
        authApi.loginResult = LoginResult.TooManyRequests(retryAfterSeconds = 30)

        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        assertEquals(AlternativeLoginError.TOO_MANY_REQUESTS, viewModel.uiState.value.alternativeLogin.error)
        assertEquals(30, viewModel.uiState.value.lockedSeconds)
        advanceSeconds(30)
        assertFalse(viewModel.uiState.value.isLocked)
    }

    @Test
    fun `TC-S1-10 sin conexion muestra error y permite reintentar`() {
        authApi.loginResult = LoginResult.NetworkError

        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        val state = viewModel.uiState.value
        assertEquals(AlternativeLoginError.NETWORK, state.alternativeLogin.error)
        assertEquals(0, state.failedAttempts)
        assertFalse(state.alternativeLogin.isSubmitting)
    }

    @Test
    fun `TC-S1-10 no envia dos veces mientras hay una solicitud en curso`() {
        authApi.pendingLogin = CompletableDeferred()

        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        assertTrue(viewModel.uiState.value.alternativeLogin.isSubmitting)
        assertEquals(1, authApi.loginCount)
    }

    // Recuperación de contraseña por SMS (HU-MOV-02)

    @Test
    fun `recuperar contrasena envia el codigo y muestra el codigo de prueba`() {
        viewModel.openPasswordRecovery()
        authApi.forgotResult = OtpResult.Sent(debugCode = "123456")

        viewModel.requestRecoveryCode(" maria.ruiz@correo.co ")

        val state = viewModel.uiState.value
        assertTrue(state.showPasswordRecovery)
        assertTrue(state.recovery.codeSent)
        assertEquals("123456", state.recovery.debugCode)
        assertEquals("maria.ruiz@correo.co", authApi.lastForgotEmail)
        assertEquals(60, state.otpCooldownSeconds)
    }

    @Test
    fun `recuperar contrasena exige que las contrasenas coincidan sin llamar al servidor`() {
        viewModel.openPasswordRecovery()

        viewModel.resetPassword(EMAIL, "123456", "NuevaClave2026", "OtraClave2026")

        assertEquals(RecoveryError.PASSWORD_MISMATCH, viewModel.uiState.value.recovery.error)
        assertEquals(0, authApi.resetCount)
    }

    @Test
    fun `recuperar contrasena levanta la suspension, desvincula esa cuenta y limpia el correo`() {
        repository.save(DeviceCredential("device-pedro", "s"), repository.encryptionCipher(), PEDRO, "Pedro Gómez")
        authApi.loginResult = LoginResult.Locked(retryAfterSeconds = 900)
        viewModel.onAlternativeAccessSelected()
        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())
        viewModel.openPasswordRecovery()

        viewModel.resetPassword(EMAIL, "123456", "NuevaClave2026", "NuevaClave2026")

        val state = viewModel.uiState.value
        assertTrue(state.recovery.completed)
        assertFalse(state.isLocked)
        assertFalse(repository.isBound(EMAIL))
        assertTrue(repository.isBound(PEDRO))

        viewModel.closePasswordRecovery()
        assertFalse(viewModel.uiState.value.showPasswordRecovery)
        assertTrue(viewModel.uiState.value.showAlternativeAccess)
        assertNull(viewModel.uiState.value.prefillEmail)
    }

    @Test
    fun `recuperar contrasena informa codigo invalido y clave debil`() {
        viewModel.openPasswordRecovery()

        authApi.resetResult = ResetResult.InvalidCode
        viewModel.resetPassword(EMAIL, "000000", "NuevaClave2026", "NuevaClave2026")
        assertEquals(RecoveryError.INVALID_CODE, viewModel.uiState.value.recovery.error)

        authApi.resetResult = ResetResult.WeakPassword
        viewModel.resetPassword(EMAIL, "123456", "corta", "corta")
        assertEquals(RecoveryError.WEAK_PASSWORD, viewModel.uiState.value.recovery.error)
        assertTrue(repository.isBound(EMAIL))
    }

    @Test
    fun `recuperar contrasena rechaza repetir la contrasena actual`() {
        viewModel.openPasswordRecovery()
        authApi.resetResult = ResetResult.SamePassword

        viewModel.resetPassword(EMAIL, "123456", PASSWORD, PASSWORD)

        assertEquals(RecoveryError.SAME_PASSWORD, viewModel.uiState.value.recovery.error)
        assertFalse(viewModel.uiState.value.recovery.completed)
    }

    @Test
    fun `requisitos de la contrasena nueva`() {
        assertFalse(passwordRulesMet("corta1", "corta1"))
        assertFalse(passwordRulesMet("sinnumeros", "sinnumeros"))
        assertFalse(passwordRulesMet("NuevaClave2026", "OtraClave2026"))
        assertTrue(passwordRulesMet("NuevaClave2026", "NuevaClave2026"))
    }

    // TC-S1-12: cierre de sesión seguro y revocación (HU-MOV-12)

    private fun loggedIn() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())
        assertTrue(viewModel.uiState.value.isAuthenticated)
    }

    @Test
    fun `TC-S1-12 cerrar sesion pide confirmacion antes de borrar nada`() {
        loggedIn()

        viewModel.requestLogout()

        assertTrue(viewModel.uiState.value.showLogoutConfirmation)
        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertEquals(newTokens, repository.activeSession)
    }

    @Test
    fun `TC-S1-12 cancelar la confirmacion conserva la sesion`() {
        loggedIn()
        viewModel.requestLogout()

        viewModel.cancelLogout()

        assertFalse(viewModel.uiState.value.showLogoutConfirmation)
        assertEquals(newTokens, repository.activeSession)
    }

    @Test
    fun `TC-S1-12 confirmar purga los tokens y revoca el refresh token en el servidor`() {
        loggedIn()
        viewModel.requestLogout()

        viewModel.confirmLogout()

        assertFalse(viewModel.uiState.value.isAuthenticated)
        assertNull(repository.activeSession)
        assertEquals(newTokens.refreshToken, authApi.lastRevokedToken)
    }

    @Test
    fun `TC-S1-12 la huella sigue activa despues de cerrar sesion`() {
        loggedIn()
        viewModel.requestLogout()
        viewModel.confirmLogout()
        assertEquals(AuthStatus.LOGGED_OUT_BIOMETRIC_READY, viewModel.uiState.value.status)
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertEquals(1, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-12 sin red igual purga la sesion local`() {
        authApi.logoutResult = false
        loggedIn()

        viewModel.requestLogout()
        viewModel.confirmLogout()

        assertNull(repository.activeSession)
        assertFalse(viewModel.uiState.value.isAuthenticated)
    }

    @Test
    fun `TC-S1-12 desactivar la huella revoca el telefono y borra la llave si no quedan cuentas`() {
        loggedIn()

        viewModel.disableBiometrics()

        assertFalse(viewModel.uiState.value.biometricEnabled)
        assertFalse(repository.hasStoredSession())
        assertNull(crypto.key)
        assertEquals("device-123", authApi.lastRevokedDevice)
    }

    @Test
    fun `TC-S1-12 sin huella activa cerrar sesion pide contrasena para volver`() {
        loggedIn()
        viewModel.disableBiometrics()
        viewModel.requestLogout()
        viewModel.confirmLogout()
        val authenticator = FakeBiometricAuthenticator()

        assertEquals(AuthStatus.LOGGED_OUT, viewModel.uiState.value.status)
        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.NO_STORED_SESSION, viewModel.uiState.value.status)
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-12 sin sesion activa no se ofrece cerrar sesion`() {
        viewModel.requestLogout()

        assertFalse(viewModel.uiState.value.showLogoutConfirmation)
    }

    // Casos de borde

    @Test
    fun `sensor no disponible durante el dialogo`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.Unavailable))

        assertEquals(AuthStatus.BIOMETRIC_UNAVAILABLE, viewModel.uiState.value.status)
    }

    @Test
    fun `limite del servidor al entrar con huella se informa como sin conexion`() {
        authApi.biometricResult = LoginResult.TooManyRequests(30)

        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        assertEquals(AuthStatus.SERVER_UNREACHABLE, viewModel.uiState.value.status)
    }

    @Test
    fun `ya autenticado no vuelve a pedir la huella`() {
        loggedIn()
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `activar la huella sin sesion activa solo termina el ingreso`() {
        viewModel.enableBiometricUnlock(FakeBiometricAuthenticator())

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertNull(authApi.lastRegisterToken)
    }

    @Test
    fun `si el servidor no vincula el telefono se entra sin huella`() {
        withoutBoundAccounts()
        authApi.registerFails = true
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        viewModel.enableBiometricUnlock(FakeBiometricAuthenticator())

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertFalse(repository.hasStoredSession())
    }

    @Test
    fun `si el keystore falla al activar la huella se revoca el telefono`() {
        withoutBoundAccounts()
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        viewModel.enableBiometricUnlock(FakeBiometricAuthenticator(failure = IllegalStateException("keystore")))

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertFalse(repository.hasStoredSession())
        assertEquals(registeredCredential.deviceId, authApi.lastRevokedDevice)
    }

    @Test
    fun `desactivar la huella sin sesion no hace nada`() {
        viewModel.disableBiometrics()

        assertTrue(repository.isBound(EMAIL))
        assertNull(authApi.lastRevokedDevice)
    }

    @Test
    fun `desactivar la huella de una cuenta sin huella no llama al servidor`() {
        withoutBoundAccounts()
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())
        viewModel.skipBiometricEnrollment()

        viewModel.disableBiometrics()

        assertNull(authApi.lastRevokedDevice)
    }

    @Test
    fun `codigo de recuperacion respeta la espera y los errores del servidor`() {
        viewModel.openPasswordRecovery()
        viewModel.requestRecoveryCode(EMAIL)
        viewModel.requestRecoveryCode(EMAIL)
        assertEquals(EMAIL, authApi.lastForgotEmail)

        val cases = mapOf(
            OtpResult.TooManyRequests(20) to RecoveryError.TOO_MANY_REQUESTS,
            OtpResult.SendFailed to RecoveryError.SMS_UNAVAILABLE,
            OtpResult.Failed to RecoveryError.NETWORK,
        )
        cases.forEach { (result, error) ->
            advanceSeconds(60)
            authApi.forgotResult = result
            viewModel.requestRecoveryCode(PEDRO)
            assertEquals(error, viewModel.uiState.value.recovery.error)
        }
    }

    @Test
    fun `cambiar la contrasena informa limite y falta de conexion`() {
        viewModel.openPasswordRecovery()

        authApi.resetResult = ResetResult.TooManyRequests(10)
        viewModel.resetPassword(EMAIL, "123456", "NuevaClave2026", "NuevaClave2026")
        assertEquals(RecoveryError.TOO_MANY_REQUESTS, viewModel.uiState.value.recovery.error)

        authApi.resetResult = ResetResult.NetworkError
        viewModel.resetPassword(EMAIL, "123456", "NuevaClave2026", "NuevaClave2026")
        assertEquals(RecoveryError.NETWORK, viewModel.uiState.value.recovery.error)
    }

    @Test
    fun `no envia dos cambios de contrasena a la vez`() {
        viewModel.openPasswordRecovery()
        authApi.pendingReset = CompletableDeferred()

        viewModel.resetPassword(EMAIL, "123456", "NuevaClave2026", "NuevaClave2026")
        viewModel.resetPassword(EMAIL, "123456", "NuevaClave2026", "NuevaClave2026")

        assertEquals(1, authApi.resetCount)
    }

    @Test
    fun `un segundo bloqueo reinicia la cuenta regresiva`() {
        authApi.loginResult = LoginResult.Locked(retryAfterSeconds = 100)
        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())
        advanceSeconds(100)

        authApi.loginResult = LoginResult.Locked(retryAfterSeconds = 300)
        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())

        assertEquals(300, viewModel.uiState.value.lockedSeconds)
    }

    private inner class FakeAuthApi : AuthApi {
        var otpResult: OtpResult = OtpResult.Sent(debugCode = null)
        var forgotResult: OtpResult = OtpResult.Sent(debugCode = null)
        var loginResult: LoginResult = LoginResult.Success(newTokens, "María Ruiz")
        var biometricResult: LoginResult = LoginResult.Success(newTokens, "María Ruiz")
        var resetResult: ResetResult = ResetResult.Success
        var pendingLogin: CompletableDeferred<LoginResult>? = null
        var logoutResult = true

        var lastOtpEmail: String? = null
        var lastForgotEmail: String? = null
        var lastRevokedToken: String? = null
        var lastBiometricCredential: DeviceCredential? = null
        var lastRegisterToken: String? = null
        var lastRevokedDevice: String? = null
        var otpCount = 0
        var loginCount = 0
        var resetCount = 0

        override suspend fun requestOtp(email: String): OtpResult {
            otpCount++
            lastOtpEmail = email
            return otpResult
        }

        override suspend fun login(email: String, password: String, otpCode: String): LoginResult {
            loginCount++
            return pendingLogin?.await() ?: loginResult
        }

        override suspend fun logout(refreshToken: String): Boolean {
            lastRevokedToken = refreshToken
            return logoutResult
        }

        var registerResult: DeviceCredential? = null
        var registerFails = false

        override suspend fun registerDevice(accessToken: String): DeviceCredential? {
            lastRegisterToken = accessToken
            return if (registerFails) null else registerResult ?: registeredCredential
        }

        override suspend fun biometricLogin(credential: DeviceCredential): LoginResult {
            lastBiometricCredential = credential
            return biometricResult
        }

        override suspend fun revokeDevice(accessToken: String, deviceId: String): Boolean {
            lastRevokedDevice = deviceId
            return true
        }

        override suspend fun forgotPassword(email: String): OtpResult {
            lastForgotEmail = email
            return forgotResult
        }

        var pendingReset: CompletableDeferred<ResetResult>? = null

        override suspend fun resetPassword(email: String, code: String, newPassword: String): ResetResult {
            resetCount++
            return pendingReset?.await() ?: resetResult
        }
    }

    private companion object {
        const val EMAIL = "maria.ruiz@correo.co"
        const val PEDRO = "pedro.gomez@correo.co"
        const val PASSWORD = "Solventa2026!"
        const val OTP = "417902"
    }

    private class FakeBiometricAuthenticator(
        private val availability: BiometricAvailability = BiometricAvailability.AVAILABLE,
        private val result: BiometricResult? = null,
        private val deferred: CompletableDeferred<BiometricResult>? = null,
        private val failure: Exception? = null,
    ) : BiometricAuthenticator {
        var promptCount = 0
            private set
        var lastCipher: Cipher? = null
            private set

        override fun checkAvailability(): BiometricAvailability = availability

        override suspend fun authenticate(cipher: Cipher): BiometricResult {
            promptCount++
            lastCipher = cipher
            failure?.let { throw it }
            return deferred?.await() ?: result ?: BiometricResult.Success(cipher)
        }
    }
}

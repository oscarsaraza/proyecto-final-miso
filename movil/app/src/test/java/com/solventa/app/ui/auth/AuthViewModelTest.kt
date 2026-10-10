package com.solventa.app.ui.auth

import com.solventa.app.data.session.FakeSessionCrypto
import com.solventa.app.data.session.InMemorySessionStore
import com.solventa.app.data.session.SecureSessionRepository
import com.solventa.app.domain.auth.AuthApi
import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult
import com.solventa.app.domain.auth.LoginResult
import com.solventa.app.domain.auth.OtpResult
import com.solventa.app.domain.auth.SessionTokens
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import javax.crypto.Cipher

@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {

    private val tokens = SessionTokens("access.jwt.token", "refresh-token-123")

    private lateinit var crypto: FakeSessionCrypto
    private lateinit var store: InMemorySessionStore
    private lateinit var repository: SecureSessionRepository
    private lateinit var authApi: FakeAuthApi
    private lateinit var viewModel: AuthViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        crypto = FakeSessionCrypto()
        store = InMemorySessionStore()
        SecureSessionRepository(crypto, store).apply { save(tokens, encryptionCipher()) }
        repository = SecureSessionRepository(crypto, store)
        authApi = FakeAuthApi()
        viewModel = AuthViewModel(repository, authApi)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `debe inicializar el estado de UI con valores predeterminados`() {
        val state = viewModel.uiState.value
        assertFalse(state.isAuthenticated)
        assertEquals(0, state.failedAttempts)
        assertFalse(state.isLocked)
        assertEquals(AuthStatus.IDLE, state.status)
        assertFalse(state.showAlternativeAccess)
    }

    // TC-S1-09: autenticación biométrica (HU-MOV-01)

    @Test
    fun `TC-S1-09 autenticacion biometrica exitosa desbloquea la sesion guardada`() {
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        val state = viewModel.uiState.value
        assertTrue(state.isAuthenticated)
        assertEquals(AuthStatus.AUTHENTICATED, state.status)
        assertEquals(tokens, repository.activeSession)
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
        assertFalse(viewModel.uiState.value.isAuthenticated)
        assertNull(repository.activeSession)

        viewModel.authenticateWithBiometrics(authenticator)
        assertEquals(2, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 boton de contrasena del dialogo lleva al acceso alternativo`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.UseAlternative))

        val state = viewModel.uiState.value
        assertTrue(state.showAlternativeAccess)
        assertFalse(state.isAuthenticated)
    }

    @Test
    fun `TC-S1-09 sin biometria registrada no abre el dialogo`() {
        val authenticator = FakeBiometricAuthenticator(availability = BiometricAvailability.NOT_ENROLLED)

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.BIOMETRIC_NOT_ENROLLED, viewModel.uiState.value.status)
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 sin sensor biometrico no abre el dialogo`() {
        val authenticator = FakeBiometricAuthenticator(availability = BiometricAvailability.UNAVAILABLE)

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.BIOMETRIC_UNAVAILABLE, viewModel.uiState.value.status)
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 bloqueo del sensor por intentos fallidos no autentica`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.LockedOut))

        assertEquals(AuthStatus.BIOMETRIC_LOCKED_OUT, viewModel.uiState.value.status)
        assertFalse(viewModel.uiState.value.isAuthenticated)
    }

    @Test
    fun `TC-S1-09 error inesperado del sensor no autentica`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.Error(code = 99)))

        assertEquals(AuthStatus.BIOMETRIC_ERROR, viewModel.uiState.value.status)
        assertFalse(viewModel.uiState.value.isAuthenticated)
    }

    // TC-S1-11: sesión custodiada en el Keystore (HU-MOV-03)

    @Test
    fun `TC-S1-11 sin sesion guardada pide ingresar primero con contrasena`() {
        store.clear()
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.NO_STORED_SESSION, viewModel.uiState.value.status)
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-11 llave invalidada reinicia la sesion sin abrir el dialogo`() {
        crypto.invalidated = true
        val authenticator = FakeBiometricAuthenticator()

        viewModel.authenticateWithBiometrics(authenticator)

        assertEquals(AuthStatus.SESSION_RESET, viewModel.uiState.value.status)
        assertFalse(repository.hasStoredSession())
        assertEquals(0, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-11 sesion alterada se descarta y no autentica`() {
        val stored = checkNotNull(store.stored)
        stored.ciphertext[0] = (stored.ciphertext[0].toInt() xor 0x01).toByte()

        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator())

        assertEquals(AuthStatus.SESSION_RESET, viewModel.uiState.value.status)
        assertFalse(viewModel.uiState.value.isAuthenticated)
        assertFalse(repository.hasStoredSession())
    }

    @Test
    fun `volver desde el acceso alternativo restablece la pantalla biometrica`() {
        viewModel.onAlternativeAccessSelected()
        assertTrue(viewModel.uiState.value.showAlternativeAccess)

        viewModel.onBackToBiometrics()

        assertFalse(viewModel.uiState.value.showAlternativeAccess)
        assertEquals(AuthStatus.IDLE, viewModel.uiState.value.status)
    }

    // TC-S1-10: acceso alternativo con contraseña y segundo factor (HU-MOV-02)

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
    fun `TC-S1-10 fallo al solicitar codigo muestra error de conexion`() {
        authApi.otpResult = OtpResult.Failed

        viewModel.requestOtp(EMAIL)

        assertEquals(AlternativeLoginError.NETWORK, viewModel.uiState.value.alternativeLogin.error)
    }

    @Test
    fun `TC-S1-10 login correcto con biometria disponible ofrece activarla`() {
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        val state = viewModel.uiState.value
        assertTrue(state.offerBiometricEnrollment)
        assertFalse(state.isAuthenticated)
        assertEquals("María Ruiz", state.fullName)
        assertEquals(newTokens, repository.activeSession)
    }

    @Test
    fun `TC-S1-10 login correcto sin biometria entra directo`() {
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
    fun `TC-S1-10 activar biometria guarda la sesion cifrada para el siguiente ingreso`() {
        store.clear()
        val authenticator = FakeBiometricAuthenticator()
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, authenticator)

        viewModel.enableBiometricUnlock(authenticator)

        assertTrue(viewModel.uiState.value.isAuthenticated)
        val reopened = SecureSessionRepository(crypto, store)
        assertEquals(newTokens, reopened.unlock(checkNotNull(reopened.decryptionCipher())))
    }

    @Test
    fun `TC-S1-10 rechazar la biometria entra sin guardar la sesion`() {
        store.clear()
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        viewModel.skipBiometricEnrollment()

        assertTrue(viewModel.uiState.value.isAuthenticated)
        assertFalse(repository.hasStoredSession())
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
    fun `TC-S1-10 cuenta bloqueada impide nuevos intentos`() {
        authApi.loginResult = LoginResult.Locked

        viewModel.authenticateWithPassword(EMAIL, "otra", "000000", FakeBiometricAuthenticator())
        viewModel.authenticateWithPassword(EMAIL, PASSWORD, OTP, FakeBiometricAuthenticator())

        assertTrue(viewModel.uiState.value.isLocked)
        assertEquals(AlternativeLoginError.ACCOUNT_LOCKED, viewModel.uiState.value.alternativeLogin.error)
        assertEquals(1, authApi.loginCount)
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

    @Test
    fun `logout debe lanzar NotImplementedError antes de HU-MOV-12`() {
        val exception = assertThrows(NotImplementedError::class.java) {
            viewModel.logout()
        }
        assertTrue(exception.message?.contains("HU-MOV-12") == true)
    }

    private val newTokens = SessionTokens("new.access.jwt", "new-refresh")

    private inner class FakeAuthApi : AuthApi {
        var otpResult: OtpResult = OtpResult.Sent(debugCode = null)
        var loginResult: LoginResult = LoginResult.Success(newTokens, "María Ruiz")
        var pendingLogin: CompletableDeferred<LoginResult>? = null
        var lastOtpEmail: String? = null
            private set
        var loginCount = 0
            private set

        override suspend fun requestOtp(email: String): OtpResult {
            lastOtpEmail = email
            return otpResult
        }

        override suspend fun login(email: String, password: String, otpCode: String): LoginResult {
            loginCount++
            return pendingLogin?.await() ?: loginResult
        }
    }

    private companion object {
        const val EMAIL = "maria.ruiz@correo.co"
        const val PASSWORD = "Solventa2026!"
        const val OTP = "417902"
    }

    private class FakeBiometricAuthenticator(
        private val availability: BiometricAvailability = BiometricAvailability.AVAILABLE,
        private val result: BiometricResult? = null,
        private val deferred: CompletableDeferred<BiometricResult>? = null,
    ) : BiometricAuthenticator {
        var promptCount = 0
            private set
        var lastCipher: Cipher? = null
            private set

        override fun checkAvailability(): BiometricAvailability = availability

        override suspend fun authenticate(cipher: Cipher): BiometricResult {
            promptCount++
            lastCipher = cipher
            return deferred?.await() ?: result ?: BiometricResult.Success(cipher)
        }
    }
}

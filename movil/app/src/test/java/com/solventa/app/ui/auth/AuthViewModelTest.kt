package com.solventa.app.ui.auth

import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {

    private lateinit var viewModel: AuthViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        viewModel = AuthViewModel()
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `debe inicializar el estado de UI con valores predeterminados`() {
        val state = viewModel.uiState.value
        assertNotNull(state)
        assertFalse(state.isAuthenticated)
        assertEquals(0, state.failedAttempts)
        assertFalse(state.isLocked)
        assertEquals(AuthStatus.IDLE, state.status)
        assertFalse(state.showAlternativeAccess)
    }

    // TC-S1-09: Autenticación biométrica (HU-MOV-01)

    @Test
    fun `TC-S1-09 autenticacion biometrica exitosa da acceso a la app`() {
        val authenticator = FakeBiometricAuthenticator(result = BiometricResult.Success)

        viewModel.authenticateWithBiometrics(authenticator)

        val state = viewModel.uiState.value
        assertTrue(state.isAuthenticated)
        assertEquals(AuthStatus.AUTHENTICATED, state.status)
        assertEquals(1, authenticator.promptCount)
    }

    @Test
    fun `TC-S1-09 muestra estado de verificacion mientras el dialogo esta abierto`() {
        val pending = CompletableDeferred<BiometricResult>()
        val authenticator = FakeBiometricAuthenticator(deferred = pending)

        viewModel.authenticateWithBiometrics(authenticator)
        assertEquals(AuthStatus.AUTHENTICATING, viewModel.uiState.value.status)

        pending.complete(BiometricResult.Success)
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
    fun `TC-S1-09 sin biometria registrada no abre el dialogo y orienta al acceso alternativo`() {
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

        val state = viewModel.uiState.value
        assertEquals(AuthStatus.BIOMETRIC_LOCKED_OUT, state.status)
        assertFalse(state.isAuthenticated)
    }

    @Test
    fun `TC-S1-09 error inesperado del sensor no autentica`() {
        viewModel.authenticateWithBiometrics(FakeBiometricAuthenticator(result = BiometricResult.Error(code = 99)))

        val state = viewModel.uiState.value
        assertEquals(AuthStatus.BIOMETRIC_ERROR, state.status)
        assertFalse(state.isAuthenticated)
    }

    @Test
    fun `volver desde el acceso alternativo restablece la pantalla biometrica`() {
        viewModel.onAlternativeAccessSelected()
        assertTrue(viewModel.uiState.value.showAlternativeAccess)

        viewModel.onBackToBiometrics()

        val state = viewModel.uiState.value
        assertFalse(state.showAlternativeAccess)
        assertEquals(AuthStatus.IDLE, state.status)
    }

    @Test
    fun `authenticateWithPin debe lanzar NotImplementedError antes de HU-MOV-02`() {
        val exception = assertThrows(NotImplementedError::class.java) {
            viewModel.authenticateWithPin("1234")
        }
        assertTrue(exception.message?.contains("HU-MOV-02") == true)
    }

    @Test
    fun `logout debe lanzar NotImplementedError antes de HU-MOV-12`() {
        val exception = assertThrows(NotImplementedError::class.java) {
            viewModel.logout()
        }
        assertTrue(exception.message?.contains("HU-MOV-12") == true)
    }

    private class FakeBiometricAuthenticator(
        private val availability: BiometricAvailability = BiometricAvailability.AVAILABLE,
        private val result: BiometricResult = BiometricResult.Success,
        private val deferred: CompletableDeferred<BiometricResult>? = null,
    ) : BiometricAuthenticator {
        var promptCount = 0
            private set

        override fun checkAvailability(): BiometricAvailability = availability

        override suspend fun authenticate(): BiometricResult {
            promptCount++
            return deferred?.await() ?: result
        }
    }
}

package com.solventa.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.solventa.app.data.session.SecureSessionRepository
import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.crypto.Cipher

enum class AuthStatus {
    IDLE,
    AUTHENTICATING,
    AUTHENTICATED,
    CANCELLED,
    BIOMETRIC_UNAVAILABLE,
    BIOMETRIC_NOT_ENROLLED,
    BIOMETRIC_LOCKED_OUT,
    BIOMETRIC_ERROR,
    NO_STORED_SESSION,
    SESSION_RESET,
}

data class AuthUiState(
    val isAuthenticated: Boolean = false,
    val failedAttempts: Int = 0,
    val isLocked: Boolean = false,
    val status: AuthStatus = AuthStatus.IDLE,
    val showAlternativeAccess: Boolean = false,
)

/**
 * ViewModel de autenticación biométrica y acceso alternativo (HU-MOV-01, HU-MOV-02, HU-MOV-12).
 */
class AuthViewModel(
    private val sessionRepository: SecureSessionRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    fun authenticateWithBiometrics(authenticator: BiometricAuthenticator) {
        val current = _uiState.value
        if (current.isAuthenticated || current.status == AuthStatus.AUTHENTICATING) return

        when (authenticator.checkAvailability()) {
            BiometricAvailability.NOT_ENROLLED -> {
                _uiState.update { it.copy(status = AuthStatus.BIOMETRIC_NOT_ENROLLED) }
                return
            }
            BiometricAvailability.UNAVAILABLE -> {
                _uiState.update { it.copy(status = AuthStatus.BIOMETRIC_UNAVAILABLE) }
                return
            }
            BiometricAvailability.AVAILABLE -> Unit
        }

        if (!sessionRepository.hasStoredSession()) {
            _uiState.update { it.copy(status = AuthStatus.NO_STORED_SESSION) }
            return
        }
        val cipher = sessionRepository.decryptionCipher()
        if (cipher == null) {
            _uiState.update { it.copy(status = AuthStatus.SESSION_RESET) }
            return
        }

        _uiState.update { it.copy(status = AuthStatus.AUTHENTICATING) }
        viewModelScope.launch {
            val result = authenticator.authenticate(cipher)
            val status = when (result) {
                is BiometricResult.Success -> unlockSession(result.cipher)
                BiometricResult.Cancelled -> AuthStatus.CANCELLED
                BiometricResult.UseAlternative -> AuthStatus.IDLE
                BiometricResult.LockedOut -> AuthStatus.BIOMETRIC_LOCKED_OUT
                BiometricResult.Unavailable -> AuthStatus.BIOMETRIC_UNAVAILABLE
                is BiometricResult.Error -> AuthStatus.BIOMETRIC_ERROR
            }
            _uiState.update { state ->
                state.copy(
                    status = status,
                    isAuthenticated = status == AuthStatus.AUTHENTICATED,
                    showAlternativeAccess = state.showAlternativeAccess || result is BiometricResult.UseAlternative,
                )
            }
        }
    }

    private fun unlockSession(authenticatedCipher: Cipher): AuthStatus =
        try {
            sessionRepository.unlock(authenticatedCipher)
            AuthStatus.AUTHENTICATED
        } catch (e: Exception) {
            sessionRepository.clear()
            AuthStatus.SESSION_RESET
        }

    fun onAlternativeAccessSelected() {
        _uiState.update { it.copy(showAlternativeAccess = true) }
    }

    fun onBackToBiometrics() {
        _uiState.update { it.copy(showAlternativeAccess = false, status = AuthStatus.IDLE) }
    }

    /**
     * Acceso alternativo por PIN de respaldo con bloqueo a los 3 intentos (Placeholder para HU-MOV-02 / TC-S1-10).
     */
    fun authenticateWithPin(pin: String) {
        throw NotImplementedError("HU-MOV-02: Acceso alternativo por PIN pendiente de implementación")
    }

    /**
     * Cierre de sesión seguro y borrado de secretos (Placeholder para HU-MOV-12 / TC-S1-12).
     */
    fun logout() {
        throw NotImplementedError("HU-MOV-12: Cierre de sesión seguro pendiente de implementación")
    }
}

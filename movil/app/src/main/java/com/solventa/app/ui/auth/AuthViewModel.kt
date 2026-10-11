package com.solventa.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.solventa.app.data.session.SecureSessionRepository
import com.solventa.app.domain.auth.AuthApi
import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult
import com.solventa.app.domain.auth.LoginResult
import com.solventa.app.domain.auth.OtpResult
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
    LOGGED_OUT,
}

enum class AlternativeLoginError {
    INVALID_CREDENTIALS,
    ACCOUNT_LOCKED,
    NETWORK,
}

data class AlternativeLoginState(
    val isSubmitting: Boolean = false,
    val otpSent: Boolean = false,
    val debugOtpCode: String? = null,
    val error: AlternativeLoginError? = null,
)

data class AuthUiState(
    val isAuthenticated: Boolean = false,
    val failedAttempts: Int = 0,
    val isLocked: Boolean = false,
    val status: AuthStatus = AuthStatus.IDLE,
    val showAlternativeAccess: Boolean = false,
    val alternativeLogin: AlternativeLoginState = AlternativeLoginState(),
    val offerBiometricEnrollment: Boolean = false,
    val fullName: String? = null,
    val showLogoutConfirmation: Boolean = false,
)

/**
 * ViewModel de autenticación biométrica y acceso alternativo (HU-MOV-01, HU-MOV-02, HU-MOV-12).
 */
class AuthViewModel(
    private val sessionRepository: SecureSessionRepository,
    private val authApi: AuthApi,
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

    fun requestOtp(email: String) {
        viewModelScope.launch {
            val result = authApi.requestOtp(email.trim())
            _uiState.update { state ->
                val form = when (result) {
                    is OtpResult.Sent -> state.alternativeLogin.copy(otpSent = true, debugOtpCode = result.debugCode, error = null)
                    OtpResult.Failed -> state.alternativeLogin.copy(error = AlternativeLoginError.NETWORK)
                }
                state.copy(alternativeLogin = form)
            }
        }
    }

    fun authenticateWithPassword(
        email: String,
        password: String,
        otpCode: String,
        authenticator: BiometricAuthenticator,
    ) {
        val current = _uiState.value
        if (current.isLocked || current.alternativeLogin.isSubmitting) return

        _uiState.update { it.copy(alternativeLogin = it.alternativeLogin.copy(isSubmitting = true, error = null)) }
        viewModelScope.launch {
            val result = authApi.login(email.trim(), password, otpCode.trim())
            val canEnrollBiometrics = result is LoginResult.Success &&
                authenticator.checkAvailability() == BiometricAvailability.AVAILABLE
            if (result is LoginResult.Success) sessionRepository.startSession(result.tokens)

            _uiState.update { state ->
                val form = state.alternativeLogin.copy(isSubmitting = false)
                when (result) {
                    is LoginResult.Success -> state.copy(
                        alternativeLogin = form,
                        failedAttempts = 0,
                        fullName = result.fullName,
                        offerBiometricEnrollment = canEnrollBiometrics,
                        isAuthenticated = !canEnrollBiometrics,
                        status = if (canEnrollBiometrics) state.status else AuthStatus.AUTHENTICATED,
                    )
                    LoginResult.InvalidCredentials -> state.copy(
                        alternativeLogin = form.copy(error = AlternativeLoginError.INVALID_CREDENTIALS),
                        failedAttempts = state.failedAttempts + 1,
                    )
                    LoginResult.Locked -> state.copy(
                        alternativeLogin = form.copy(error = AlternativeLoginError.ACCOUNT_LOCKED),
                        isLocked = true,
                    )
                    LoginResult.NetworkError -> state.copy(
                        alternativeLogin = form.copy(error = AlternativeLoginError.NETWORK),
                    )
                }
            }
        }
    }

    // Activar la biometría cifra la sesión con la llave del Keystore (HU-MOV-03).
    fun enableBiometricUnlock(authenticator: BiometricAuthenticator) {
        val tokens = sessionRepository.activeSession ?: return finishLogin()
        viewModelScope.launch {
            try {
                val result = authenticator.authenticate(sessionRepository.encryptionCipher())
                if (result is BiometricResult.Success) sessionRepository.save(tokens, result.cipher)
            } catch (e: Exception) {
                sessionRepository.clear()
                sessionRepository.startSession(tokens)
            }
            finishLogin()
        }
    }

    fun skipBiometricEnrollment() = finishLogin()

    private fun finishLogin() {
        _uiState.update {
            it.copy(
                offerBiometricEnrollment = false,
                isAuthenticated = true,
                status = AuthStatus.AUTHENTICATED,
                showAlternativeAccess = false,
            )
        }
    }

    fun requestLogout() {
        if (_uiState.value.isAuthenticated) _uiState.update { it.copy(showLogoutConfirmation = true) }
    }

    fun cancelLogout() {
        _uiState.update { it.copy(showLogoutConfirmation = false) }
    }

    // Primero se purga lo local; la revocación en el servidor es de mejor esfuerzo si no hay red.
    fun confirmLogout() {
        val refreshToken = sessionRepository.activeSession?.refreshToken
        sessionRepository.clear()
        _uiState.value = AuthUiState(status = AuthStatus.LOGGED_OUT)
        if (refreshToken != null) {
            viewModelScope.launch { authApi.logout(refreshToken) }
        }
    }
}

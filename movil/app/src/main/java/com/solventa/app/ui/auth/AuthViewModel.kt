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
import com.solventa.app.domain.auth.ResetResult
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
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
    LOGGED_OUT_BIOMETRIC_READY,
    ACCOUNT_LOCKED,
    SERVER_UNREACHABLE,
}

enum class AlternativeLoginError {
    INVALID_CREDENTIALS,
    INVALID_FORMAT,
    ACCOUNT_LOCKED,
    TOO_MANY_REQUESTS,
    SMS_UNAVAILABLE,
    NETWORK,
}

enum class RecoveryError {
    INVALID_CODE,
    WEAK_PASSWORD,
    PASSWORD_MISMATCH,
    TOO_MANY_REQUESTS,
    SMS_UNAVAILABLE,
    NETWORK,
}

data class AlternativeLoginState(
    val isSubmitting: Boolean = false,
    val otpSent: Boolean = false,
    val debugOtpCode: String? = null,
    val error: AlternativeLoginError? = null,
)

data class PasswordRecoveryState(
    val codeSent: Boolean = false,
    val debugCode: String? = null,
    val isSubmitting: Boolean = false,
    val completed: Boolean = false,
    val error: RecoveryError? = null,
)

data class AuthUiState(
    val isAuthenticated: Boolean = false,
    val failedAttempts: Int = 0,
    val lockedSeconds: Int = 0,
    val otpCooldownSeconds: Int = 0,
    val status: AuthStatus = AuthStatus.IDLE,
    val showAlternativeAccess: Boolean = false,
    val alternativeLogin: AlternativeLoginState = AlternativeLoginState(),
    val showPasswordRecovery: Boolean = false,
    val recovery: PasswordRecoveryState = PasswordRecoveryState(),
    val offerBiometricEnrollment: Boolean = false,
    val biometricEnabled: Boolean = false,
    val fullName: String? = null,
    val showLogoutConfirmation: Boolean = false,
) {
    val isLocked: Boolean get() = lockedSeconds > 0
}

/**
 * Acceso con huella, acceso alterno con contraseña y código, recuperación de contraseña y
 * cierre de sesión (HU-MOV-01, HU-MOV-02, HU-MOV-03, HU-MOV-12).
 */
class AuthViewModel(
    private val sessionRepository: SecureSessionRepository,
    private val authApi: AuthApi,
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState(biometricEnabled = sessionRepository.hasStoredSession()))
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    private var lockJob: Job? = null
    private var otpCooldownJob: Job? = null

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
            _uiState.update { it.copy(status = AuthStatus.NO_STORED_SESSION, biometricEnabled = false) }
            return
        }
        val cipher = sessionRepository.decryptionCipher()
        if (cipher == null) {
            _uiState.update { it.copy(status = AuthStatus.SESSION_RESET, biometricEnabled = false) }
            return
        }

        _uiState.update { it.copy(status = AuthStatus.AUTHENTICATING) }
        viewModelScope.launch {
            when (val result = authenticator.authenticate(cipher)) {
                is BiometricResult.Success -> signInWithDevice(result.cipher)
                BiometricResult.Cancelled -> setStatus(AuthStatus.CANCELLED)
                BiometricResult.UseAlternative -> _uiState.update {
                    it.copy(status = AuthStatus.IDLE, showAlternativeAccess = true)
                }
                BiometricResult.LockedOut -> setStatus(AuthStatus.BIOMETRIC_LOCKED_OUT)
                BiometricResult.Unavailable -> setStatus(AuthStatus.BIOMETRIC_UNAVAILABLE)
                is BiometricResult.Error -> setStatus(AuthStatus.BIOMETRIC_ERROR)
            }
        }
    }

    private suspend fun signInWithDevice(authenticatedCipher: Cipher) {
        val credential = try {
            sessionRepository.unlock(authenticatedCipher)
        } catch (e: Exception) {
            resetBiometrics()
            return
        }
        when (val result = authApi.biometricLogin(credential)) {
            is LoginResult.Success -> {
                sessionRepository.startSession(result.tokens)
                _uiState.update {
                    it.copy(status = AuthStatus.AUTHENTICATED, isAuthenticated = true, fullName = result.fullName)
                }
            }
            LoginResult.InvalidCredentials, LoginResult.InvalidFormat -> resetBiometrics()
            is LoginResult.Locked -> {
                setStatus(AuthStatus.ACCOUNT_LOCKED)
                startLockCountdown(result.retryAfterSeconds)
            }
            is LoginResult.TooManyRequests, LoginResult.NetworkError -> setStatus(AuthStatus.SERVER_UNREACHABLE)
        }
    }

    // El servidor ya no reconoce el teléfono (huella desactivada o contraseña cambiada).
    private fun resetBiometrics() {
        sessionRepository.unbindDevice()
        _uiState.update { it.copy(status = AuthStatus.SESSION_RESET, biometricEnabled = false) }
    }

    private fun setStatus(status: AuthStatus) {
        _uiState.update { it.copy(status = status) }
    }

    fun onAlternativeAccessSelected() {
        _uiState.update { it.copy(showAlternativeAccess = true) }
    }

    fun onBackToBiometrics() {
        _uiState.update {
            it.copy(showAlternativeAccess = false, status = AuthStatus.IDLE, alternativeLogin = AlternativeLoginState())
        }
    }

    fun requestOtp(email: String) {
        if (_uiState.value.otpCooldownSeconds > 0) return
        viewModelScope.launch {
            val result = authApi.requestOtp(email.trim())
            _uiState.update { state ->
                val form = state.alternativeLogin
                state.copy(
                    alternativeLogin = when (result) {
                        is OtpResult.Sent -> form.copy(otpSent = true, debugOtpCode = result.debugCode, error = null)
                        is OtpResult.TooManyRequests -> form.copy(error = AlternativeLoginError.TOO_MANY_REQUESTS)
                        OtpResult.SendFailed -> form.copy(error = AlternativeLoginError.SMS_UNAVAILABLE)
                        OtpResult.Failed -> form.copy(error = AlternativeLoginError.NETWORK)
                    },
                )
            }
            startOtpCooldown(result)
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
                !sessionRepository.hasStoredSession() &&
                authenticator.checkAvailability() == BiometricAvailability.AVAILABLE
            if (result is LoginResult.Success) sessionRepository.startSession(result.tokens)

            _uiState.update { state ->
                val form = state.alternativeLogin.copy(isSubmitting = false)
                when (result) {
                    is LoginResult.Success -> state.copy(
                        alternativeLogin = AlternativeLoginState(),
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
                    LoginResult.InvalidFormat -> state.copy(
                        alternativeLogin = form.copy(error = AlternativeLoginError.INVALID_FORMAT),
                    )
                    is LoginResult.Locked -> state.copy(
                        alternativeLogin = form.copy(error = AlternativeLoginError.ACCOUNT_LOCKED),
                    )
                    is LoginResult.TooManyRequests -> state.copy(
                        alternativeLogin = form.copy(error = AlternativeLoginError.TOO_MANY_REQUESTS),
                    )
                    LoginResult.NetworkError -> state.copy(
                        alternativeLogin = form.copy(error = AlternativeLoginError.NETWORK),
                    )
                }
            }
            when (result) {
                is LoginResult.Locked -> startLockCountdown(result.retryAfterSeconds)
                is LoginResult.TooManyRequests -> startLockCountdown(result.retryAfterSeconds)
                else -> Unit
            }
        }
    }

    // Activar la huella vincula el teléfono en el servidor y cifra esa credencial en el Keystore (HU-MOV-03).
    fun enableBiometricUnlock(authenticator: BiometricAuthenticator) {
        val tokens = sessionRepository.activeSession ?: return finishLogin()
        viewModelScope.launch {
            val credential = authApi.registerDevice(tokens.accessToken)
            if (credential == null) {
                finishLogin()
                return@launch
            }
            val saved = try {
                val result = authenticator.authenticate(sessionRepository.encryptionCipher())
                if (result is BiometricResult.Success) {
                    sessionRepository.save(credential, result.cipher)
                    true
                } else {
                    false
                }
            } catch (e: Exception) {
                sessionRepository.unbindDevice()
                false
            }
            if (!saved) authApi.revokeDevice(tokens.accessToken, credential.deviceId)
            _uiState.update { it.copy(biometricEnabled = saved) }
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

    fun disableBiometrics() {
        val accessToken = sessionRepository.activeSession?.accessToken
        val deviceId = sessionRepository.storedDeviceId()
        sessionRepository.unbindDevice()
        _uiState.update { it.copy(biometricEnabled = false) }
        if (accessToken != null && deviceId != null) {
            viewModelScope.launch { authApi.revokeDevice(accessToken, deviceId) }
        }
    }

    fun requestLogout() {
        if (_uiState.value.isAuthenticated) _uiState.update { it.copy(showLogoutConfirmation = true) }
    }

    fun cancelLogout() {
        _uiState.update { it.copy(showLogoutConfirmation = false) }
    }

    // Se borra la sesión del teléfono y se revoca en el servidor; la huella vinculada se conserva.
    fun confirmLogout() {
        val refreshToken = sessionRepository.activeSession?.refreshToken
        sessionRepository.endSession()
        val biometricReady = sessionRepository.hasStoredSession()
        _uiState.value = AuthUiState(
            status = if (biometricReady) AuthStatus.LOGGED_OUT_BIOMETRIC_READY else AuthStatus.LOGGED_OUT,
            biometricEnabled = biometricReady,
        )
        if (refreshToken != null) {
            viewModelScope.launch { authApi.logout(refreshToken) }
        }
    }

    fun openPasswordRecovery() {
        _uiState.update { it.copy(showPasswordRecovery = true, recovery = PasswordRecoveryState()) }
    }

    fun closePasswordRecovery() {
        _uiState.update {
            it.copy(
                showPasswordRecovery = false,
                showAlternativeAccess = true,
                recovery = PasswordRecoveryState(),
            )
        }
    }

    fun requestRecoveryCode(email: String) {
        if (_uiState.value.otpCooldownSeconds > 0) return
        viewModelScope.launch {
            val result = authApi.forgotPassword(email.trim())
            _uiState.update { state ->
                val recovery = state.recovery
                state.copy(
                    recovery = when (result) {
                        is OtpResult.Sent -> recovery.copy(codeSent = true, debugCode = result.debugCode, error = null)
                        is OtpResult.TooManyRequests -> recovery.copy(error = RecoveryError.TOO_MANY_REQUESTS)
                        OtpResult.SendFailed -> recovery.copy(error = RecoveryError.SMS_UNAVAILABLE)
                        OtpResult.Failed -> recovery.copy(error = RecoveryError.NETWORK)
                    },
                )
            }
            startOtpCooldown(result)
        }
    }

    fun resetPassword(email: String, code: String, newPassword: String, confirmation: String) {
        if (_uiState.value.recovery.isSubmitting) return
        if (newPassword != confirmation) {
            _uiState.update { it.copy(recovery = it.recovery.copy(error = RecoveryError.PASSWORD_MISMATCH)) }
            return
        }
        _uiState.update { it.copy(recovery = it.recovery.copy(isSubmitting = true, error = null)) }
        viewModelScope.launch {
            val result = authApi.resetPassword(email.trim(), code.trim(), newPassword)
            if (result == ResetResult.Success) {
                sessionRepository.unbindDevice()
                lockJob?.cancel()
            }
            _uiState.update { state ->
                val recovery = state.recovery.copy(isSubmitting = false)
                when (result) {
                    ResetResult.Success -> state.copy(
                        recovery = recovery.copy(completed = true),
                        biometricEnabled = false,
                        lockedSeconds = 0,
                        failedAttempts = 0,
                        alternativeLogin = AlternativeLoginState(),
                    )
                    ResetResult.InvalidCode -> state.copy(recovery = recovery.copy(error = RecoveryError.INVALID_CODE))
                    ResetResult.WeakPassword -> state.copy(recovery = recovery.copy(error = RecoveryError.WEAK_PASSWORD))
                    is ResetResult.TooManyRequests ->
                        state.copy(recovery = recovery.copy(error = RecoveryError.TOO_MANY_REQUESTS))
                    ResetResult.NetworkError -> state.copy(recovery = recovery.copy(error = RecoveryError.NETWORK))
                }
            }
        }
    }

    private fun startOtpCooldown(result: OtpResult) {
        val seconds = when (result) {
            is OtpResult.Sent -> OTP_COOLDOWN_SECONDS
            is OtpResult.TooManyRequests -> result.retryAfterSeconds
            else -> return
        }
        otpCooldownJob?.cancel()
        otpCooldownJob = countdown(seconds) { remaining -> _uiState.update { it.copy(otpCooldownSeconds = remaining) } }
    }

    // Al terminar la espera el botón se reactiva solo, sin cerrar la app.
    private fun startLockCountdown(seconds: Int) {
        lockJob?.cancel()
        lockJob = countdown(seconds) { remaining ->
            _uiState.update { state ->
                if (remaining > 0) {
                    state.copy(lockedSeconds = remaining)
                } else {
                    val lockErrors = setOf(AlternativeLoginError.ACCOUNT_LOCKED, AlternativeLoginError.TOO_MANY_REQUESTS)
                    state.copy(
                        lockedSeconds = 0,
                        failedAttempts = 0,
                        alternativeLogin = if (state.alternativeLogin.error in lockErrors) {
                            state.alternativeLogin.copy(error = null)
                        } else {
                            state.alternativeLogin
                        },
                        status = if (state.status == AuthStatus.ACCOUNT_LOCKED) AuthStatus.IDLE else state.status,
                    )
                }
            }
        }
    }

    private fun countdown(seconds: Int, onTick: (Int) -> Unit): Job = viewModelScope.launch {
        var remaining = seconds.coerceAtLeast(1)
        while (remaining > 0) {
            onTick(remaining)
            delay(1_000)
            remaining--
        }
        onTick(0)
    }

    private companion object {
        const val OTP_COOLDOWN_SECONDS = 60
    }
}

package com.solventa.app.ui.auth

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class AuthUiState(
    val isAuthenticated: Boolean = false,
    val failedAttempts: Int = 0,
    val isLocked: Boolean = false,
    val statusMessage: String = "Listo para autenticación"
)

/**
 * ViewModel de autenticación biométrica y PIN alternativo (HU-MOV-01, HU-MOV-02, HU-MOV-12).
 */
class AuthViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    /**
     * Autenticación mediante sensor biométrico (Placeholder para HU-MOV-01 / TC-S1-09).
     */
    fun authenticateWithBiometrics() {
        throw NotImplementedError("HU-MOV-01: Autenticación biométrica pendiente de implementación")
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

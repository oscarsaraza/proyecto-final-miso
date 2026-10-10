package com.solventa.app.domain.auth

interface BiometricAuthenticator {
    fun checkAvailability(): BiometricAvailability

    suspend fun authenticate(): BiometricResult
}

enum class BiometricAvailability {
    AVAILABLE,
    NOT_ENROLLED,
    UNAVAILABLE,
}

sealed interface BiometricResult {
    data object Success : BiometricResult
    data object Cancelled : BiometricResult
    data object UseAlternative : BiometricResult
    data object LockedOut : BiometricResult
    data object Unavailable : BiometricResult
    data class Error(val code: Int) : BiometricResult
}

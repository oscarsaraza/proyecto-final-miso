package com.solventa.app.domain.auth

import javax.crypto.Cipher

interface BiometricAuthenticator {
    fun checkAvailability(): BiometricAvailability

    suspend fun authenticate(cipher: Cipher): BiometricResult
}

enum class BiometricAvailability {
    AVAILABLE,
    NOT_ENROLLED,
    UNAVAILABLE,
}

sealed interface BiometricResult {
    class Success(val cipher: Cipher) : BiometricResult
    data object Cancelled : BiometricResult
    data object UseAlternative : BiometricResult
    data object LockedOut : BiometricResult
    data object Unavailable : BiometricResult
    data class Error(val code: Int) : BiometricResult
}

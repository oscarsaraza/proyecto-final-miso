package com.solventa.app.data.auth

import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult

internal fun availabilityFromCode(code: Int): BiometricAvailability = when (code) {
    BiometricManager.BIOMETRIC_SUCCESS -> BiometricAvailability.AVAILABLE
    BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> BiometricAvailability.NOT_ENROLLED
    else -> BiometricAvailability.UNAVAILABLE
}

internal fun resultFromErrorCode(code: Int): BiometricResult = when (code) {
    BiometricPrompt.ERROR_NEGATIVE_BUTTON -> BiometricResult.UseAlternative
    BiometricPrompt.ERROR_USER_CANCELED,
    BiometricPrompt.ERROR_CANCELED -> BiometricResult.Cancelled
    BiometricPrompt.ERROR_LOCKOUT,
    BiometricPrompt.ERROR_LOCKOUT_PERMANENT -> BiometricResult.LockedOut
    BiometricPrompt.ERROR_NO_BIOMETRICS,
    BiometricPrompt.ERROR_HW_NOT_PRESENT,
    BiometricPrompt.ERROR_HW_UNAVAILABLE -> BiometricResult.Unavailable
    else -> BiometricResult.Error(code)
}

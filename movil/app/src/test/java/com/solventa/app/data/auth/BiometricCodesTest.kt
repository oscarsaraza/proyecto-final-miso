package com.solventa.app.data.auth

import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult
import org.junit.Assert.assertEquals
import org.junit.Test

class BiometricCodesTest {

    @Test
    fun `biometria fuerte disponible`() {
        assertEquals(BiometricAvailability.AVAILABLE, availabilityFromCode(BiometricManager.BIOMETRIC_SUCCESS))
    }

    @Test
    fun `sensor sin huella ni rostro registrados`() {
        assertEquals(
            BiometricAvailability.NOT_ENROLLED,
            availabilityFromCode(BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED),
        )
    }

    @Test
    fun `sin hardware o con hardware no disponible`() {
        listOf(
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE,
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE,
            BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED,
        ).forEach { code ->
            assertEquals(BiometricAvailability.UNAVAILABLE, availabilityFromCode(code))
        }
    }

    @Test
    fun `boton negativo del dialogo lleva al acceso alternativo`() {
        assertEquals(BiometricResult.UseAlternative, resultFromErrorCode(BiometricPrompt.ERROR_NEGATIVE_BUTTON))
    }

    @Test
    fun `cancelacion por el usuario o por el sistema`() {
        assertEquals(BiometricResult.Cancelled, resultFromErrorCode(BiometricPrompt.ERROR_USER_CANCELED))
        assertEquals(BiometricResult.Cancelled, resultFromErrorCode(BiometricPrompt.ERROR_CANCELED))
    }

    @Test
    fun `bloqueo temporal y permanente del sensor`() {
        assertEquals(BiometricResult.LockedOut, resultFromErrorCode(BiometricPrompt.ERROR_LOCKOUT))
        assertEquals(BiometricResult.LockedOut, resultFromErrorCode(BiometricPrompt.ERROR_LOCKOUT_PERMANENT))
    }

    @Test
    fun `biometria no disponible durante la autenticacion`() {
        listOf(
            BiometricPrompt.ERROR_NO_BIOMETRICS,
            BiometricPrompt.ERROR_HW_NOT_PRESENT,
            BiometricPrompt.ERROR_HW_UNAVAILABLE,
        ).forEach { code ->
            assertEquals(BiometricResult.Unavailable, resultFromErrorCode(code))
        }
    }

    @Test
    fun `cualquier otro codigo se reporta como error`() {
        assertEquals(BiometricResult.Error(BiometricPrompt.ERROR_TIMEOUT), resultFromErrorCode(BiometricPrompt.ERROR_TIMEOUT))
    }
}

package com.solventa.app.data.auth

import androidx.biometric.BiometricManager
import androidx.biometric.BiometricManager.Authenticators.BIOMETRIC_STRONG
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import com.solventa.app.R
import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAvailability
import com.solventa.app.domain.auth.BiometricResult
import kotlinx.coroutines.suspendCancellableCoroutine
import javax.crypto.Cipher
import kotlin.coroutines.resume

// Solo biometría de clase 3: es la que permite atar la llave del Keystore (HU-MOV-03).
class AndroidBiometricAuthenticator(
    private val activity: FragmentActivity,
) : BiometricAuthenticator {

    override fun checkAvailability(): BiometricAvailability =
        availabilityFromCode(BiometricManager.from(activity).canAuthenticate(BIOMETRIC_STRONG))

    override suspend fun authenticate(cipher: Cipher): BiometricResult = suspendCancellableCoroutine { continuation ->
        val callback = object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                val authenticatedCipher = result.cryptoObject?.cipher
                val outcome = if (authenticatedCipher != null) {
                    BiometricResult.Success(authenticatedCipher)
                } else {
                    BiometricResult.Error(BiometricPrompt.ERROR_VENDOR)
                }
                if (continuation.isActive) continuation.resume(outcome)
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                if (continuation.isActive) continuation.resume(resultFromErrorCode(errorCode))
            }

            // onAuthenticationFailed no cierra el diálogo: el sistema reintenta y bloquea por su cuenta.
        }

        val prompt = BiometricPrompt(activity, ContextCompat.getMainExecutor(activity), callback)
        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle(activity.getString(R.string.biometric_prompt_title))
            .setSubtitle(activity.getString(R.string.biometric_prompt_subtitle))
            .setNegativeButtonText(activity.getString(R.string.biometric_prompt_negative))
            .setAllowedAuthenticators(BIOMETRIC_STRONG)
            .build()

        continuation.invokeOnCancellation { prompt.cancelAuthentication() }
        prompt.authenticate(promptInfo, BiometricPrompt.CryptoObject(cipher))
    }
}

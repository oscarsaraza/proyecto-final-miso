package com.solventa.app.domain.auth

interface AuthApi {
    suspend fun requestOtp(email: String): OtpResult
    suspend fun login(email: String, password: String, otpCode: String): LoginResult

    /** true si el servidor revocó el refresh token. */
    suspend fun logout(refreshToken: String): Boolean

    /** Vincula este teléfono para entrar con huella; null si el servidor no respondió. */
    suspend fun registerDevice(accessToken: String): DeviceCredential?
    suspend fun biometricLogin(credential: DeviceCredential): LoginResult
    suspend fun revokeDevice(accessToken: String, deviceId: String): Boolean

    suspend fun forgotPassword(email: String): OtpResult
    suspend fun resetPassword(email: String, code: String, newPassword: String): ResetResult
}

sealed interface OtpResult {
    /** [debugCode] solo llega cuando el backend simula el SMS. */
    data class Sent(val debugCode: String?) : OtpResult
    data class TooManyRequests(val retryAfterSeconds: Int) : OtpResult
    data object SendFailed : OtpResult
    data object Failed : OtpResult
}

sealed interface LoginResult {
    class Success(val tokens: SessionTokens, val fullName: String) : LoginResult
    data object InvalidCredentials : LoginResult
    data object InvalidFormat : LoginResult
    data class Locked(val retryAfterSeconds: Int) : LoginResult
    data class TooManyRequests(val retryAfterSeconds: Int) : LoginResult
    data object NetworkError : LoginResult
}

sealed interface ResetResult {
    data object Success : ResetResult
    data object InvalidCode : ResetResult
    data object WeakPassword : ResetResult
    data class TooManyRequests(val retryAfterSeconds: Int) : ResetResult
    data object NetworkError : ResetResult
}

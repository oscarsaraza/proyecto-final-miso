package com.solventa.app.domain.auth

interface AuthApi {
    suspend fun requestOtp(email: String): OtpResult
    suspend fun login(email: String, password: String, otpCode: String): LoginResult
}

sealed interface OtpResult {
    /** [debugCode] solo llega en desarrollo y reemplaza al SMS. */
    data class Sent(val debugCode: String?) : OtpResult
    data object Failed : OtpResult
}

sealed interface LoginResult {
    class Success(val tokens: SessionTokens, val fullName: String) : LoginResult
    data object InvalidCredentials : LoginResult
    data object Locked : LoginResult
    data object NetworkError : LoginResult
}

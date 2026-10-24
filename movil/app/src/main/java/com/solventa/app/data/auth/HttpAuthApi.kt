package com.solventa.app.data.auth

import com.solventa.app.domain.auth.AuthApi
import com.solventa.app.domain.auth.DeviceCredential
import com.solventa.app.domain.auth.LoginResult
import com.solventa.app.domain.auth.OtpResult
import com.solventa.app.domain.auth.ResetResult
import com.solventa.app.domain.auth.SessionTokens
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

class HttpAuthApi(private val baseUrl: String) : AuthApi {

    override suspend fun requestOtp(email: String): OtpResult =
        sendCode("auth/otp", email)

    override suspend fun forgotPassword(email: String): OtpResult =
        sendCode("auth/password/forgot", email)

    override suspend fun login(email: String, password: String, otpCode: String): LoginResult =
        tokens("auth/login", JSONObject().put("email", email).put("password", password).put("otp_code", otpCode))

    override suspend fun biometricLogin(credential: DeviceCredential): LoginResult =
        tokens(
            "auth/biometric",
            JSONObject().put("device_id", credential.deviceId).put("device_secret", credential.secret),
        )

    override suspend fun logout(refreshToken: String): Boolean = withContext(Dispatchers.IO) {
        try {
            request("POST", "auth/logout", JSONObject().put("refresh_token", refreshToken)).code ==
                HttpURLConnection.HTTP_NO_CONTENT
        } catch (e: IOException) {
            false
        }
    }

    override suspend fun registerDevice(accessToken: String): DeviceCredential? = withContext(Dispatchers.IO) {
        try {
            val response = request("POST", "auth/devices", null, accessToken)
            if (response.code != HttpURLConnection.HTTP_CREATED) return@withContext null
            val json = JSONObject(response.body)
            DeviceCredential(json.getString("device_id"), json.getString("device_secret"))
        } catch (e: IOException) {
            null
        } catch (e: JSONException) {
            null
        }
    }

    override suspend fun revokeDevice(accessToken: String, deviceId: String): Boolean = withContext(Dispatchers.IO) {
        try {
            request("DELETE", "auth/devices/$deviceId", null, accessToken).code == HttpURLConnection.HTTP_NO_CONTENT
        } catch (e: IOException) {
            false
        }
    }

    override suspend fun resetPassword(email: String, code: String, newPassword: String): ResetResult =
        withContext(Dispatchers.IO) {
            try {
                val body = JSONObject().put("email", email).put("code", code).put("new_password", newPassword)
                val response = request("POST", "auth/password/reset", body)
                when (response.code) {
                    HttpURLConnection.HTTP_OK -> ResetResult.Success
                    HttpURLConnection.HTTP_UNAUTHORIZED -> ResetResult.InvalidCode
                    HTTP_UNPROCESSABLE_ENTITY -> ResetResult.WeakPassword
                    HttpURLConnection.HTTP_CONFLICT -> ResetResult.SamePassword
                    HTTP_TOO_MANY_REQUESTS -> ResetResult.TooManyRequests(response.retryAfter)
                    else -> ResetResult.NetworkError
                }
            } catch (e: IOException) {
                ResetResult.NetworkError
            }
        }

    private suspend fun sendCode(path: String, email: String): OtpResult = withContext(Dispatchers.IO) {
        try {
            val response = request("POST", path, JSONObject().put("email", email))
            when (response.code) {
                HttpURLConnection.HTTP_OK -> {
                    val json = JSONObject(response.body)
                    OtpResult.Sent(debugCode = if (json.isNull("debug_code")) null else json.getString("debug_code"))
                }
                HTTP_TOO_MANY_REQUESTS -> OtpResult.TooManyRequests(response.retryAfter)
                HttpURLConnection.HTTP_UNAVAILABLE -> OtpResult.SendFailed
                else -> OtpResult.Failed
            }
        } catch (e: IOException) {
            OtpResult.Failed
        } catch (e: JSONException) {
            OtpResult.Failed
        }
    }

    private suspend fun tokens(path: String, body: JSONObject): LoginResult = withContext(Dispatchers.IO) {
        try {
            val response = request("POST", path, body)
            when (response.code) {
                HttpURLConnection.HTTP_OK -> {
                    val json = JSONObject(response.body)
                    LoginResult.Success(
                        tokens = SessionTokens(json.getString("access_token"), json.getString("refresh_token")),
                        fullName = json.getString("full_name"),
                    )
                }
                HttpURLConnection.HTTP_UNAUTHORIZED -> LoginResult.InvalidCredentials
                HTTP_UNPROCESSABLE_ENTITY -> LoginResult.InvalidFormat
                HTTP_LOCKED -> LoginResult.Locked(response.retryAfter)
                HTTP_TOO_MANY_REQUESTS -> LoginResult.TooManyRequests(response.retryAfter)
                else -> LoginResult.NetworkError
            }
        } catch (e: IOException) {
            LoginResult.NetworkError
        } catch (e: JSONException) {
            LoginResult.NetworkError
        }
    }

    private fun request(method: String, path: String, json: JSONObject?, bearer: String? = null): HttpResponse {
        val connection = URL(baseUrl + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = method
            connection.connectTimeout = TIMEOUT_MS
            connection.readTimeout = TIMEOUT_MS
            bearer?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
            if (json != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.use { it.write(json.toString().toByteArray(Charsets.UTF_8)) }
            }
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val retryAfter = connection.getHeaderField("Retry-After")?.toIntOrNull() ?: DEFAULT_RETRY_AFTER
            return HttpResponse(code, stream?.bufferedReader()?.use { it.readText() }.orEmpty(), retryAfter)
        } finally {
            connection.disconnect()
        }
    }

    private class HttpResponse(val code: Int, val body: String, val retryAfter: Int)

    private companion object {
        const val TIMEOUT_MS = 10_000
        const val DEFAULT_RETRY_AFTER = 60
        const val HTTP_UNPROCESSABLE_ENTITY = 422
        const val HTTP_LOCKED = 423
        const val HTTP_TOO_MANY_REQUESTS = 429
    }
}

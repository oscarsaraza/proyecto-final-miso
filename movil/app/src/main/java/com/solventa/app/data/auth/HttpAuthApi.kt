package com.solventa.app.data.auth

import com.solventa.app.domain.auth.AuthApi
import com.solventa.app.domain.auth.LoginResult
import com.solventa.app.domain.auth.OtpResult
import com.solventa.app.domain.auth.SessionTokens
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

class HttpAuthApi(private val baseUrl: String) : AuthApi {

    override suspend fun requestOtp(email: String): OtpResult = withContext(Dispatchers.IO) {
        try {
            val response = post("auth/otp", JSONObject().put("email", email))
            if (response.code != HttpURLConnection.HTTP_OK) return@withContext OtpResult.Failed
            val json = JSONObject(response.body)
            OtpResult.Sent(debugCode = if (json.isNull("debug_code")) null else json.getString("debug_code"))
        } catch (e: IOException) {
            OtpResult.Failed
        } catch (e: JSONException) {
            OtpResult.Failed
        }
    }

    override suspend fun login(email: String, password: String, otpCode: String): LoginResult =
        withContext(Dispatchers.IO) {
            try {
                val body = JSONObject().put("email", email).put("password", password).put("otp_code", otpCode)
                val response = post("auth/login", body)
                when (response.code) {
                    HttpURLConnection.HTTP_OK -> {
                        val json = JSONObject(response.body)
                        LoginResult.Success(
                            tokens = SessionTokens(json.getString("access_token"), json.getString("refresh_token")),
                            fullName = json.getString("full_name"),
                        )
                    }
                    HttpURLConnection.HTTP_UNAUTHORIZED, HTTP_UNPROCESSABLE_ENTITY -> LoginResult.InvalidCredentials
                    HTTP_LOCKED -> LoginResult.Locked
                    else -> LoginResult.NetworkError
                }
            } catch (e: IOException) {
                LoginResult.NetworkError
            } catch (e: JSONException) {
                LoginResult.NetworkError
            }
        }

    override suspend fun logout(refreshToken: String): Boolean = withContext(Dispatchers.IO) {
        try {
            post("auth/logout", JSONObject().put("refresh_token", refreshToken)).code == HttpURLConnection.HTTP_NO_CONTENT
        } catch (e: IOException) {
            false
        }
    }

    private fun post(path: String, json: JSONObject): HttpResponse {
        val connection = URL(baseUrl + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "POST"
            connection.connectTimeout = TIMEOUT_MS
            connection.readTimeout = TIMEOUT_MS
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(json.toString().toByteArray(Charsets.UTF_8)) }
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            return HttpResponse(code, stream?.bufferedReader()?.use { it.readText() }.orEmpty())
        } finally {
            connection.disconnect()
        }
    }

    private class HttpResponse(val code: Int, val body: String)

    private companion object {
        const val TIMEOUT_MS = 10_000
        const val HTTP_UNPROCESSABLE_ENTITY = 422
        const val HTTP_LOCKED = 423
    }
}

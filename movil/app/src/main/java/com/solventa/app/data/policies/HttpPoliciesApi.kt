package com.solventa.app.data.policies

import com.solventa.app.domain.policies.CoverageLimit
import com.solventa.app.domain.policies.PoliciesApi
import com.solventa.app.domain.policies.PoliciesResult
import com.solventa.app.domain.policies.PolicyCard
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.time.OffsetDateTime
import java.time.format.DateTimeParseException

class HttpPoliciesApi(private val baseUrl: String) : PoliciesApi {

    override suspend fun activePolicies(accessToken: String): PoliciesResult = withContext(Dispatchers.IO) {
        val connection = URL(baseUrl + "insured/policies").openConnection() as HttpURLConnection
        try {
            connection.connectTimeout = TIMEOUT_MS
            connection.readTimeout = TIMEOUT_MS
            connection.setRequestProperty("Authorization", "Bearer $accessToken")
            when (connection.responseCode) {
                HttpURLConnection.HTTP_OK -> {
                    val body = connection.inputStream.bufferedReader().use { it.readText() }
                    PoliciesResult.Loaded(parse(JSONObject(body)))
                }
                HttpURLConnection.HTTP_UNAUTHORIZED -> PoliciesResult.Unauthorized
                else -> PoliciesResult.Unavailable
            }
        } catch (e: IOException) {
            PoliciesResult.Unavailable
        } catch (e: JSONException) {
            PoliciesResult.Unavailable
        } catch (e: DateTimeParseException) {
            PoliciesResult.Unavailable
        } finally {
            connection.disconnect()
        }
    }

    // Solo se leen los campos de la tarjeta; cualquier otro que llegue se descarta.
    private fun parse(json: JSONObject): List<PolicyCard> {
        val policies = json.getJSONArray("policies")
        return (0 until policies.length()).map { i ->
            val policy = policies.getJSONObject(i)
            val coverages = policy.getJSONArray("coverages")
            PolicyCard(
                policyNumber = policy.getString("policy_number"),
                plan = policy.getString("plan"),
                holderName = policy.getString("holder_name"),
                coverages = (0 until coverages.length()).map { j ->
                    val coverage = coverages.getJSONObject(j)
                    CoverageLimit(coverage.getString("name"), coverage.getDouble("limit"))
                },
                validFrom = OffsetDateTime.parse(policy.getString("valid_from")).toInstant(),
                validUntil = OffsetDateTime.parse(policy.getString("valid_until")).toInstant(),
            )
        }
    }

    private companion object {
        const val TIMEOUT_MS = 10_000
    }
}

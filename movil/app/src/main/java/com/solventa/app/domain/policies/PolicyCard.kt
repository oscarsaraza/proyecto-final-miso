package com.solventa.app.domain.policies

import java.time.Instant

data class CoverageLimit(val name: String, val limit: Double)

/** Tarjeta de la billetera: solo lo que se muestra, sin documento, beneficiarios ni prima (HU-MOV-04). */
data class PolicyCard(
    val policyNumber: String,
    val plan: String,
    val holderName: String,
    val coverages: List<CoverageLimit>,
    val validFrom: Instant,
    val validUntil: Instant,
) {
    fun isExpiredAt(now: Instant): Boolean = !validUntil.isAfter(now)
}

interface PoliciesApi {
    suspend fun activePolicies(accessToken: String): PoliciesResult
}

sealed interface PoliciesResult {
    data class Loaded(val policies: List<PolicyCard>) : PoliciesResult
    data object Unauthorized : PoliciesResult
    data object Unavailable : PoliciesResult
}

/** Copia local por cuenta; null al leer significa que la cuenta aún no tiene copia. */
interface PolicyStore {
    suspend fun save(accountEmail: String, policies: List<PolicyCard>)
    suspend fun read(accountEmail: String): List<PolicyCard>?
    suspend fun delete(accountEmail: String)
}

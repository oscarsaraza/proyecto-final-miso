package com.solventa.app.data.policies

import com.solventa.app.domain.policies.CoverageLimit
import com.solventa.app.domain.policies.PoliciesApi
import com.solventa.app.domain.policies.PoliciesResult
import com.solventa.app.domain.policies.PolicyCard
import com.solventa.app.domain.policies.PolicyStore
import java.time.Instant

class InMemoryPolicyStore : PolicyStore {
    val copies = mutableMapOf<String, List<PolicyCard>>()

    override suspend fun save(accountEmail: String, policies: List<PolicyCard>) {
        copies[accountEmail] = policies
    }

    override suspend fun read(accountEmail: String): List<PolicyCard>? = copies[accountEmail]

    override suspend fun delete(accountEmail: String) {
        copies.remove(accountEmail)
    }
}

class FakePoliciesApi(var result: PoliciesResult = PoliciesResult.Loaded(emptyList())) : PoliciesApi {
    var lastToken: String? = null

    override suspend fun activePolicies(accessToken: String): PoliciesResult {
        lastToken = accessToken
        return result
    }
}

fun samplePolicy(number: String = "POL-2026-00001", validUntil: String = "2027-01-01T00:00:00Z") = PolicyCard(
    policyNumber = number,
    plan = "premium",
    holderName = "María Ruiz",
    coverages = listOf(CoverageLimit("Responsabilidad civil", 1e8)),
    validFrom = Instant.parse("2026-01-01T00:00:00Z"),
    validUntil = Instant.parse(validUntil),
)

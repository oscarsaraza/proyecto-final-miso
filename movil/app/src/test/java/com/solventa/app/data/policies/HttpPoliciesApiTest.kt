package com.solventa.app.data.policies

import com.solventa.app.domain.policies.CoverageLimit
import com.solventa.app.domain.policies.PoliciesResult
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.time.Instant

// Contrato de la billetera con el BFF del asegurado (HU-MOV-04: TC-03).
@RunWith(RobolectricTestRunner::class)
class HttpPoliciesApiTest {

    private lateinit var server: MockWebServer
    private lateinit var api: HttpPoliciesApi

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
        api = HttpPoliciesApi(server.url("/api/v1/").toString())
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `TC-03 pide las polizas con el token y guarda solo los campos de la tarjeta`() = runTest {
        server.enqueue(
            MockResponse().setResponseCode(200).setBody(
                """
                {"policies": [{
                  "policy_number": "POL-2026-00001", "plan": "premium", "holder_name": "María Ruiz",
                  "coverages": [{"name": "Responsabilidad civil", "limit": 100000000.0, "deductible": 0}],
                  "valid_from": "2026-01-01T00:00:00Z", "valid_until": "2027-01-01T00:00:00+00:00",
                  "insured_document": "1020304050", "beneficiaries": [{"name": "Beneficiaria"}]
                }]}
                """.trimIndent()
            )
        )

        val result = api.activePolicies("token-de-prueba") as PoliciesResult.Loaded

        val request = server.takeRequest()
        assertEquals("GET", request.method)
        assertEquals("/api/v1/insured/policies", request.path)
        assertEquals("Bearer token-de-prueba", request.getHeader("Authorization"))
        val card = result.policies.single()
        assertEquals("POL-2026-00001", card.policyNumber)
        assertEquals("premium", card.plan)
        assertEquals("María Ruiz", card.holderName)
        assertEquals(listOf(CoverageLimit("Responsabilidad civil", 1e8)), card.coverages)
        assertEquals(Instant.parse("2026-01-01T00:00:00Z"), card.validFrom)
        assertEquals(Instant.parse("2027-01-01T00:00:00Z"), card.validUntil)
        assertEquals(card, card.toEntity().toCard())
        assertEquals(false, card.toEntity().toString().contains("1020304050"))
    }

    @Test
    fun `401 es sesion vencida`() = runTest {
        server.enqueue(MockResponse().setResponseCode(401))

        assertEquals(PoliciesResult.Unauthorized, api.activePolicies("token"))
    }

    @Test
    fun `errores del servidor o respuestas mal formadas se tratan como sin conexion`() = runTest {
        server.enqueue(MockResponse().setResponseCode(503))
        server.enqueue(MockResponse().setResponseCode(200).setBody("{\"policies\": [{\"plan\": \"basic\"}]}"))
        server.enqueue(MockResponse().setResponseCode(403))

        repeat(3) { assertEquals(PoliciesResult.Unavailable, api.activePolicies("token")) }
    }

    @Test
    fun `sin red responde sin conexion`() = runTest {
        server.shutdown()

        assertEquals(PoliciesResult.Unavailable, api.activePolicies("token"))
    }
}

package com.solventa.app.ui.wallet

import com.solventa.app.data.policies.FakePoliciesApi
import com.solventa.app.data.policies.InMemoryPolicyStore
import com.solventa.app.data.policies.samplePolicy
import com.solventa.app.domain.policies.PoliciesResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset

// Billetera de pólizas con y sin conexión (HU-MOV-04: TC-04, TC-05, TC-07).
@OptIn(ExperimentalCoroutinesApi::class)
class WalletViewModelTest {

    private val now = Instant.parse("2026-10-22T12:00:00Z")
    private val active = samplePolicy("POL-2026-00001", "2027-01-01T00:00:00Z")
    private val other = samplePolicy("POL-2026-00002", "2027-03-01T00:00:00Z")

    private lateinit var api: FakePoliciesApi
    private lateinit var store: InMemoryPolicyStore
    private lateinit var viewModel: WalletViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        api = FakePoliciesApi()
        store = InMemoryPolicyStore()
        viewModel = WalletViewModel(api, store, Clock.fixed(now, ZoneOffset.UTC))
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `TC-04 con red muestra las polizas del servidor y guarda la copia de la cuenta`() {
        api.result = PoliciesResult.Loaded(listOf(active, other))

        viewModel.open(EMAIL, "token")

        val state = viewModel.uiState.value
        assertEquals(listOf(active, other), state.policies.map { it.policy })
        assertFalse(state.offline)
        assertFalse(state.loading)
        assertEquals("token", api.lastToken)
        assertEquals(listOf(active, other), store.copies[EMAIL])
    }

    @Test
    fun `TC-04 sin polizas vigentes lo indica y la copia queda vacia`() {
        api.result = PoliciesResult.Loaded(emptyList())

        viewModel.open(EMAIL, "token")

        assertTrue(viewModel.uiState.value.empty)
        assertEquals(emptyList<Any>(), store.copies[EMAIL])
    }

    @Test
    fun `TC-05 sin red y con copia muestra la copia con el aviso de sin conexion`() {
        store.copies[EMAIL] = listOf(active)

        viewModel.open(EMAIL, null)

        val state = viewModel.uiState.value
        assertTrue(state.offline)
        assertFalse(state.needsConnection)
        assertEquals(listOf(active), state.policies.map { it.policy })
        assertNull(api.lastToken)
    }

    @Test
    fun `TC-05 sin red y sin copia indica que necesita conexion para la primera descarga`() {
        viewModel.open(EMAIL, null)

        val state = viewModel.uiState.value
        assertTrue(state.needsConnection)
        assertFalse(state.empty)
    }

    @Test
    fun `TC-05 con el servidor caido usa la copia con el aviso de sin conexion`() {
        api.result = PoliciesResult.Unavailable
        store.copies[EMAIL] = listOf(active)

        viewModel.open(EMAIL, "token")

        val state = viewModel.uiState.value
        assertTrue(state.offline)
        assertEquals(listOf(active), state.policies.map { it.policy })
        assertEquals(listOf(active), store.copies[EMAIL])
    }

    @Test
    fun `TC-05 una poliza de la copia que vencio sin red aparece como vencida`() {
        val expired = samplePolicy("POL-2025-00009", "2026-10-22T12:00:00Z")
        store.copies[EMAIL] = listOf(expired, active)

        viewModel.open(EMAIL, null)

        assertEquals(listOf(true, false), viewModel.uiState.value.policies.map { it.expired })
    }

    @Test
    fun `TC-07 un 401 borra la copia de la cuenta y marca la sesion vencida`() {
        api.result = PoliciesResult.Unauthorized
        store.copies[EMAIL] = listOf(active)
        store.copies[OTHER_EMAIL] = listOf(other)

        viewModel.open(EMAIL, "token")

        val state = viewModel.uiState.value
        assertTrue(state.sessionExpired)
        assertTrue(state.policies.isEmpty())
        assertFalse(EMAIL in store.copies)
        assertTrue(OTHER_EMAIL in store.copies)
    }

    @Test
    fun `TC-07 cada cuenta ve solo su copia`() {
        store.copies[EMAIL] = listOf(active)
        store.copies[OTHER_EMAIL] = listOf(other)

        viewModel.open(OTHER_EMAIL, null)

        assertEquals(listOf(other), viewModel.uiState.value.policies.map { it.policy })
    }

    private companion object {
        const val EMAIL = "maria.ruiz@correo.co"
        const val OTHER_EMAIL = "otra.cuenta@example.com"
    }
}

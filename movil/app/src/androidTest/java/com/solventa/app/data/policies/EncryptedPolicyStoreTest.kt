package com.solventa.app.data.policies

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.solventa.app.domain.policies.CoverageLimit
import com.solventa.app.domain.policies.PolicyCard
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.time.Instant

// Copia cifrada con SQLCipher y el Keystore real del emulador (HU-MOV-04: TC-06).
@RunWith(AndroidJUnit4::class)
class EncryptedPolicyStoreTest {

    private val context: Context = ApplicationProvider.getApplicationContext()
    private val keys = KeystoreWalletKeys()
    private val store = EncryptedPolicyStore(context, PassphraseVault(context, keys))
    private val policy = PolicyCard(
        policyNumber = "POL-2026-07777",
        plan = "standard",
        holderName = "Asegurado de Prueba",
        coverages = listOf(CoverageLimit("Responsabilidad civil", 1e8)),
        validFrom = Instant.parse("2026-01-01T00:00:00Z"),
        validUntil = Instant.parse("2027-01-01T00:00:00Z"),
    )

    @After
    fun tearDown() = runTest {
        store.delete(EMAIL)
        store.delete(OTHER_EMAIL)
    }

    @Test
    fun guarda_y_lee_la_copia_de_cada_cuenta() = runTest {
        store.save(EMAIL, listOf(policy))

        assertEquals(listOf(policy), store.read(EMAIL))
        assertNull(store.read(OTHER_EMAIL))
    }

    @Test
    fun el_archivo_no_es_sqlite_legible_ni_contiene_el_numero_de_poliza() = runTest {
        store.save(EMAIL, listOf(policy))

        val file = context.getDatabasePath("wallet_${PassphraseVault.accountId(EMAIL)}.db")
        val bytes = file.readBytes()
        assertFalse(String(bytes.copyOfRange(0, 16), Charsets.US_ASCII).startsWith("SQLite format 3"))
        assertFalse(String(bytes, Charsets.ISO_8859_1).contains(policy.policyNumber))
        assertFalse(file.name.contains("correo"))
    }

    @Test
    fun sin_la_llave_de_la_cuenta_la_copia_no_abre_y_se_borra() = runTest {
        store.save(EMAIL, listOf(policy))
        keys.delete("solventa_wallet_${PassphraseVault.accountId(EMAIL)}")

        assertNull(store.read(EMAIL))
        assertFalse(context.getDatabasePath("wallet_${PassphraseVault.accountId(EMAIL)}.db").exists())
    }

    @Test
    fun borrar_la_cuenta_elimina_su_archivo_y_conserva_las_demas() = runTest {
        store.save(EMAIL, listOf(policy))
        store.save(OTHER_EMAIL, emptyList())

        store.delete(EMAIL)

        assertNull(store.read(EMAIL))
        assertTrue(store.read(OTHER_EMAIL)!!.isEmpty())
    }

    private companion object {
        const val EMAIL = "maria.ruiz@correo.co"
        const val OTHER_EMAIL = "otra.cuenta@example.com"
    }
}

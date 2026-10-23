package com.solventa.app.data.policies

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

// Frase de la base guardada solo envuelta por la llave de su cuenta (HU-MOV-04: CRY-01, CRY-02).
@RunWith(RobolectricTestRunner::class)
class PassphraseVaultTest {

    private class XorWalletKeys : WalletKeys {
        val aliases = mutableSetOf<String>()

        override fun wrap(alias: String, plaintext: ByteArray): WrappedSecret {
            aliases += alias
            return WrappedSecret(byteArrayOf(1), plaintext.map { (it.toInt() xor 0x5A).toByte() }.toByteArray())
        }

        override fun unwrap(alias: String, wrapped: WrappedSecret): ByteArray? =
            if (alias in aliases) wrapped.ciphertext.map { (it.toInt() xor 0x5A).toByte() }.toByteArray() else null

        override fun delete(alias: String) {
            aliases -= alias
        }
    }

    private val context: Context = ApplicationProvider.getApplicationContext()
    private lateinit var keys: XorWalletKeys
    private lateinit var vault: PassphraseVault

    @Before
    fun setUp() {
        keys = XorWalletKeys()
        vault = PassphraseVault(context, keys)
    }

    @Test
    fun `crea una frase aleatoria de 32 bytes por cuenta y solo guarda su version envuelta`() {
        val first = vault.create(ACCOUNT)
        val second = vault.create(OTHER_ACCOUNT)

        assertEquals(32, first.size)
        assertFalse(first.contentEquals(second))
        assertArrayEquals(first, vault.existing(ACCOUNT))
        val stored = context.getSharedPreferences("solventa_wallet", Context.MODE_PRIVATE).all.values.joinToString()
        assertFalse(stored.contains(java.util.Base64.getEncoder().encodeToString(first)))
    }

    @Test
    fun `borrar la cuenta elimina su frase y su llave sin tocar las demas`() {
        vault.create(ACCOUNT)
        vault.create(OTHER_ACCOUNT)

        vault.delete(ACCOUNT)

        assertNull(vault.existing(ACCOUNT))
        assertTrue(vault.existing(OTHER_ACCOUNT) != null)
        assertEquals(setOf("solventa_wallet_$OTHER_ACCOUNT"), keys.aliases)
    }

    @Test
    fun `sin la llave del Keystore la frase envuelta no se recupera`() {
        vault.create(ACCOUNT)
        keys.aliases.clear()

        assertNull(vault.existing(ACCOUNT))
    }

    @Test
    fun `el identificador de la cuenta no deja el correo y no distingue mayusculas`() {
        val id = PassphraseVault.accountId(" Maria.Ruiz@Correo.co ")

        assertEquals(PassphraseVault.accountId("maria.ruiz@correo.co"), id)
        assertEquals(32, id.length)
        assertFalse(id.contains("maria"))
    }

    private companion object {
        val ACCOUNT = PassphraseVault.accountId("maria.ruiz@correo.co")
        val OTHER_ACCOUNT = PassphraseVault.accountId("otra.cuenta@example.com")
    }
}

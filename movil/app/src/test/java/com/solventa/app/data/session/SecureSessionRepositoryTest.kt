package com.solventa.app.data.session

import com.solventa.app.domain.auth.SessionTokens
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import javax.crypto.AEADBadTagException

// TC-S1-11: custodia de credenciales en el almacén protegido (HU-MOV-03)
class SecureSessionRepositoryTest {

    private val tokens = SessionTokens(accessToken = "access.jwt.token", refreshToken = "refresh-token-123")

    private lateinit var crypto: FakeSessionCrypto
    private lateinit var store: InMemorySessionStore
    private lateinit var repository: SecureSessionRepository

    @Before
    fun setUp() {
        crypto = FakeSessionCrypto()
        store = InMemorySessionStore()
        repository = SecureSessionRepository(crypto, store)
    }

    @Test
    fun `TC-S1-11 sin sesion guardada no hay nada que desbloquear`() {
        assertFalse(repository.hasStoredSession())
        assertNull(repository.decryptionCipher())
        assertNull(repository.activeSession)
    }

    @Test
    fun `TC-S1-11 guarda los tokens cifrados y nunca en texto plano`() {
        repository.save(tokens, repository.encryptionCipher())

        val stored = checkNotNull(store.stored)
        val persisted = String(stored.ciphertext, Charsets.ISO_8859_1)
        assertFalse(persisted.contains(tokens.accessToken))
        assertFalse(persisted.contains(tokens.refreshToken))
        assertEquals(12, stored.iv.size)
        assertTrue(repository.hasStoredSession())
        assertEquals(tokens, repository.activeSession)
    }

    @Test
    fun `TC-S1-11 desbloquea la sesion con el cipher autenticado`() {
        repository.save(tokens, repository.encryptionCipher())
        val reopened = SecureSessionRepository(crypto, store)

        val unlocked = reopened.unlock(checkNotNull(reopened.decryptionCipher()))

        assertEquals(tokens, unlocked)
        assertEquals(tokens, reopened.activeSession)
    }

    @Test
    fun `TC-S1-11 llave invalidada por cambio de biometria descarta la sesion`() {
        repository.save(tokens, repository.encryptionCipher())
        crypto.invalidated = true

        assertNull(repository.decryptionCipher())
        assertFalse(repository.hasStoredSession())
    }

    @Test
    fun `TC-S1-11 sesion alterada no se puede descifrar`() {
        repository.save(tokens, repository.encryptionCipher())
        val stored = checkNotNull(store.stored)
        stored.ciphertext[0] = (stored.ciphertext[0].toInt() xor 0x01).toByte()

        assertThrows(AEADBadTagException::class.java) {
            repository.unlock(checkNotNull(repository.decryptionCipher()))
        }
    }

    @Test
    fun `TC-S1-11 clear borra la sesion, la llave y la copia en memoria`() {
        repository.save(tokens, repository.encryptionCipher())

        repository.clear()

        assertFalse(repository.hasStoredSession())
        assertNull(repository.activeSession)
        assertNull(crypto.key)
    }

    @Test
    fun `los tokens no se exponen al imprimirlos`() {
        assertEquals("SessionTokens(***)", tokens.toString())
    }
}

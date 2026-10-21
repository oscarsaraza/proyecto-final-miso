package com.solventa.app.data.session

import com.solventa.app.domain.auth.DeviceCredential
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

    private val credential = DeviceCredential(deviceId = "device-123", secret = "secreto-del-dispositivo")
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
    fun `TC-S1-11 sin huella vinculada no hay nada que desbloquear`() {
        assertFalse(repository.hasStoredSession())
        assertNull(repository.decryptionCipher())
        assertNull(repository.activeSession)
    }

    @Test
    fun `TC-S1-11 guarda la credencial cifrada y nunca el secreto en texto plano`() {
        repository.save(credential, repository.encryptionCipher())

        val stored = checkNotNull(store.stored)
        assertFalse(String(stored.ciphertext, Charsets.ISO_8859_1).contains(credential.secret))
        assertEquals(12, stored.iv.size)
        assertEquals("device-123", repository.storedDeviceId())
        assertTrue(repository.hasStoredSession())
    }

    @Test
    fun `TC-S1-11 desbloquea la credencial con el cipher autenticado`() {
        repository.save(credential, repository.encryptionCipher())
        val reopened = SecureSessionRepository(crypto, store)

        assertEquals(credential, reopened.unlock(checkNotNull(reopened.decryptionCipher())))
    }

    @Test
    fun `TC-S1-11 llave invalidada por cambio de biometria descarta la credencial`() {
        repository.save(credential, repository.encryptionCipher())
        crypto.invalidated = true

        assertNull(repository.decryptionCipher())
        assertFalse(repository.hasStoredSession())
    }

    @Test
    fun `TC-S1-11 credencial alterada no se puede descifrar`() {
        repository.save(credential, repository.encryptionCipher())
        val stored = checkNotNull(store.stored)
        stored.ciphertext[0] = (stored.ciphertext[0].toInt() xor 0x01).toByte()

        assertThrows(AEADBadTagException::class.java) {
            repository.unlock(checkNotNull(repository.decryptionCipher()))
        }
    }

    @Test
    fun `TC-S1-12 terminar la sesion conserva la huella vinculada`() {
        repository.startSession(tokens)
        repository.save(credential, repository.encryptionCipher())

        repository.endSession()

        assertNull(repository.activeSession)
        assertTrue(repository.hasStoredSession())
    }

    @Test
    fun `TC-S1-11 desvincular borra la credencial y la llave`() {
        repository.startSession(tokens)
        repository.save(credential, repository.encryptionCipher())

        repository.clear()

        assertFalse(repository.hasStoredSession())
        assertNull(repository.activeSession)
        assertNull(crypto.key)
    }

    @Test
    fun `los tokens y el secreto no se exponen al imprimirlos`() {
        assertEquals("SessionTokens(***)", tokens.toString())
        assertEquals("DeviceCredential(device-123, ***)", credential.toString())
    }
}

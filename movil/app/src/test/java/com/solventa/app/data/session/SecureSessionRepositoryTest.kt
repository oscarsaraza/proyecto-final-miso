package com.solventa.app.data.session

import com.solventa.app.domain.auth.DeviceCredential
import com.solventa.app.domain.auth.SessionTokens
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import javax.crypto.AEADBadTagException

// TC-S1-11: custodia de credenciales en el almacén protegido (HU-MOV-03)
class SecureSessionRepositoryTest {

    private val maria = DeviceCredential(deviceId = "device-maria", secret = "secreto-maria")
    private val pedro = DeviceCredential(deviceId = "device-pedro", secret = "secreto-pedro")
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

    private fun bind(credential: DeviceCredential, email: String, name: String) =
        repository.save(credential, repository.encryptionCipher(), email, name)

    @Test
    fun `TC-S1-11 sin huella vinculada no hay nada que desbloquear`() {
        assertFalse(repository.hasStoredSession())
        assertNull(repository.decryptionCipher(MARIA))
        assertNull(repository.activeSession)
    }

    @Test
    fun `TC-S1-11 guarda la credencial cifrada y nunca el secreto en texto plano`() {
        bind(maria, MARIA, "María Ruiz")

        val stored = store.sessions.single()
        assertFalse(String(stored.ciphertext, Charsets.ISO_8859_1).contains(maria.secret))
        assertEquals(12, stored.iv.size)
        assertEquals("device-maria", repository.storedDeviceId(MARIA))
        assertEquals(listOf(BoundAccount(MARIA, "María Ruiz")), repository.boundAccounts())
    }

    @Test
    fun `TC-S1-11 cada cuenta desbloquea su propia credencial`() {
        bind(maria, MARIA, "María Ruiz")
        bind(pedro, PEDRO, "Pedro Gómez")
        val reopened = SecureSessionRepository(crypto, store)

        assertEquals(maria, reopened.unlock(MARIA, checkNotNull(reopened.decryptionCipher(MARIA))))
        assertEquals(pedro, reopened.unlock(PEDRO, checkNotNull(reopened.decryptionCipher(PEDRO))))
    }

    @Test
    fun `TC-S1-11 volver a activar la huella reemplaza la credencial de esa cuenta`() {
        bind(maria, MARIA, "María Ruiz")
        bind(DeviceCredential("device-nuevo", "otro"), MARIA, "María Ruiz")

        assertEquals(1, repository.boundAccounts().size)
        assertEquals("device-nuevo", repository.storedDeviceId(MARIA))
    }

    @Test
    fun `TC-S1-11 llave invalidada por cambio de huellas descarta todas las cuentas`() {
        bind(maria, MARIA, "María Ruiz")
        bind(pedro, PEDRO, "Pedro Gómez")
        crypto.invalidated = true

        assertNull(repository.decryptionCipher(MARIA))
        assertFalse(repository.hasStoredSession())
    }

    @Test
    fun `TC-S1-11 credencial alterada no se puede descifrar`() {
        bind(maria, MARIA, "María Ruiz")
        val stored = store.sessions.single()
        stored.ciphertext[0] = (stored.ciphertext[0].toInt() xor 0x01).toByte()

        assertThrows(AEADBadTagException::class.java) {
            repository.unlock(MARIA, checkNotNull(repository.decryptionCipher(MARIA)))
        }
    }

    @Test
    fun `TC-S1-12 terminar la sesion conserva las huellas vinculadas`() {
        repository.startSession(tokens)
        bind(maria, MARIA, "María Ruiz")

        repository.endSession()

        assertNull(repository.activeSession)
        assertTrue(repository.isBound(MARIA))
    }

    @Test
    fun `desvincular una cuenta conserva las demas y la llave`() {
        bind(maria, MARIA, "María Ruiz")
        bind(pedro, PEDRO, "Pedro Gómez")

        repository.unbind(MARIA)

        assertFalse(repository.isBound(MARIA))
        assertTrue(repository.isBound(PEDRO))
        assertNotNull(crypto.key)
    }

    @Test
    fun `desvincular la ultima cuenta borra la llave`() {
        bind(maria, MARIA, "María Ruiz")

        repository.unbind(MARIA)

        assertFalse(repository.hasStoredSession())
        assertNull(crypto.key)
    }

    @Test
    fun `los tokens y el secreto no se exponen al imprimirlos`() {
        assertEquals("SessionTokens(***)", tokens.toString())
        assertEquals("DeviceCredential(device-maria, ***)", maria.toString())
    }

    private companion object {
        const val MARIA = "maria.ruiz@correo.co"
        const val PEDRO = "pedro.gomez@correo.co"
    }
}

package com.solventa.app.data.session

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

// Persistencia de las cuentas con huella en el teléfono (HU-MOV-03).
@RunWith(RobolectricTestRunner::class)
class SharedPreferencesSessionStoreTest {

    private val context: Context = ApplicationProvider.getApplicationContext()
    private lateinit var store: SharedPreferencesSessionStore

    private fun session(email: String, name: String, deviceId: String = "device-$name") =
        EncryptedSession(byteArrayOf(1, 2, 3), byteArrayOf(9, 8, 7), deviceId, email, name)

    @Before
    fun setUp() {
        store = SharedPreferencesSessionStore(context)
        store.clear()
    }

    @Test
    fun `guarda varias cuentas y las lee al reabrir`() {
        store.write(session("maria@correo.co", "María"))
        store.write(session("pedro@correo.co", "Pedro"))

        val reopened = SharedPreferencesSessionStore(context).readAll()

        assertEquals(listOf("maria@correo.co", "pedro@correo.co"), reopened.map { it.accountEmail })
        assertEquals("María", reopened.first().accountName)
        assertArrayEquals(byteArrayOf(1, 2, 3), reopened.first().ciphertext)
        assertArrayEquals(byteArrayOf(9, 8, 7), reopened.first().iv)
    }

    @Test
    fun `volver a guardar una cuenta la reemplaza`() {
        store.write(session("maria@correo.co", "María", deviceId = "viejo"))
        store.write(session("maria@correo.co", "María", deviceId = "nuevo"))

        assertEquals(listOf("nuevo"), store.readAll().map { it.deviceId })
    }

    @Test
    fun `quitar una cuenta conserva las demas y limpiar las borra todas`() {
        store.write(session("maria@correo.co", "María"))
        store.write(session("pedro@correo.co", "Pedro"))

        store.remove("maria@correo.co")
        assertEquals(listOf("pedro@correo.co"), store.readAll().map { it.accountEmail })

        store.clear()
        assertTrue(store.readAll().isEmpty())
    }

    @Test
    fun `datos dañados se ignoran sin romper la app`() {
        context.getSharedPreferences("solventa_session", Context.MODE_PRIVATE)
            .edit().putString("accounts", "no-es-json").commit()

        assertTrue(store.readAll().isEmpty())
    }
}

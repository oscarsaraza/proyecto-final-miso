package com.solventa.app.data.local

import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class EncryptedStorageManagerTest {

    private lateinit var storageManager: EncryptedStorageManager

    @Before
    fun setUp() {
        storageManager = EncryptedStorageManager()
    }

    @Test
    fun `debe instanciar el gestor de almacenamiento seguro`() {
        assertNotNull(storageManager)
        assertFalse(storageManager.isStorageInitialized())
    }

    @Test
    fun `initializeEncryptedDatabase debe lanzar NotImplementedError antes de HU-MOV-03`() {
        val exception = assertThrows(NotImplementedError::class.java) {
            storageManager.initializeEncryptedDatabase("passphrase".toByteArray())
        }
        assertTrue(exception.message?.contains("HU-MOV-03") == true)
    }
}

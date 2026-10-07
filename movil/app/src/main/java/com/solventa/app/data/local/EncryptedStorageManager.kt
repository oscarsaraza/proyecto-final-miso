package com.solventa.app.data.local

/**
 * Gestor de persistencia local protegida con SQLCipher (HU-MOV-03 / TC-S1-11).
 */
class EncryptedStorageManager {

    /**
     * Inicializa base de datos SQLite cifrada con SQLCipher.
     *
     * Placeholder a ser implementado durante HU-MOV-03.
     */
    fun initializeEncryptedDatabase(passphrase: ByteArray) {
        throw NotImplementedError("HU-MOV-03: Almacén local protegido con SQLCipher pendiente de implementación")
    }

    /**
     * Verifica el estado del almacén local.
     */
    fun isStorageInitialized(): Boolean {
        return false
    }
}

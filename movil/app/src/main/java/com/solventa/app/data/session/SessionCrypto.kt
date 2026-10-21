package com.solventa.app.data.session

import javax.crypto.Cipher

interface SessionCrypto {
    fun encryptionCipher(): Cipher

    /** Devuelve null si la llave ya no existe o fue invalidada por un cambio en la biometría. */
    fun decryptionCipher(iv: ByteArray): Cipher?

    fun deleteKey()
}

/** Credencial cifrada de una cuenta vinculada; el correo y el nombre son públicos, el secreto no. */
class EncryptedSession(
    val ciphertext: ByteArray,
    val iv: ByteArray,
    val deviceId: String,
    val accountEmail: String,
    val accountName: String,
)

interface EncryptedSessionStore {
    fun readAll(): List<EncryptedSession>

    /** Reemplaza la credencial de la misma cuenta si ya existía. */
    fun write(session: EncryptedSession)

    fun remove(accountEmail: String)

    fun clear()
}

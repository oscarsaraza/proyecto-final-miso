package com.solventa.app.data.session

import javax.crypto.Cipher

interface SessionCrypto {
    fun encryptionCipher(): Cipher

    /** Devuelve null si la llave ya no existe o fue invalidada por un cambio en la biometría. */
    fun decryptionCipher(iv: ByteArray): Cipher?

    fun deleteKey()
}

class EncryptedSession(val ciphertext: ByteArray, val iv: ByteArray)

interface EncryptedSessionStore {
    fun read(): EncryptedSession?
    fun write(session: EncryptedSession)
    fun clear()
}

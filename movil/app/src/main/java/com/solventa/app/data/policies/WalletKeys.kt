package com.solventa.app.data.policies

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.GeneralSecurityException
import java.security.KeyStore
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class WrappedSecret(val iv: ByteArray, val ciphertext: ByteArray)

interface WalletKeys {
    fun wrap(alias: String, plaintext: ByteArray): WrappedSecret

    /** null si la llave ya no existe, fue invalidada o el teléfono está bloqueado. */
    fun unwrap(alias: String, wrapped: WrappedSecret): ByteArray?

    fun delete(alias: String)
}

// Una llave AES-GCM por cuenta que no sale del Keystore y solo funciona con el teléfono desbloqueado (CRY-02).
class KeystoreWalletKeys : WalletKeys {

    private val keyStore: KeyStore by lazy { KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) } }

    override fun wrap(alias: String, plaintext: ByteArray): WrappedSecret {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, existingKey(alias) ?: generateKey(alias))
        return WrappedSecret(cipher.iv, cipher.doFinal(plaintext))
    }

    override fun unwrap(alias: String, wrapped: WrappedSecret): ByteArray? {
        val key = existingKey(alias) ?: return null
        return try {
            Cipher.getInstance(TRANSFORMATION)
                .apply { init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(GCM_TAG_BITS, wrapped.iv)) }
                .doFinal(wrapped.ciphertext)
        } catch (e: GeneralSecurityException) {
            null
        }
    }

    override fun delete(alias: String) {
        if (keyStore.containsAlias(alias)) keyStore.deleteEntry(alias)
    }

    private fun existingKey(alias: String): SecretKey? = keyStore.getKey(alias, null) as SecretKey?

    private fun generateKey(alias: String): SecretKey {
        val spec = KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .setUnlockedDeviceRequired(true)
            .build()
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
            .apply { init(spec) }
            .generateKey()
    }

    private companion object {
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val GCM_TAG_BITS = 128
    }
}

/** Frase aleatoria de la base de cada cuenta, guardada solo envuelta por su llave del Keystore (CRY-01). */
class PassphraseVault(context: Context, private val keys: WalletKeys) {

    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val random = SecureRandom()

    fun existing(accountId: String): ByteArray? {
        val iv = prefs.getString("$accountId.iv", null) ?: return null
        val ciphertext = prefs.getString("$accountId.ct", null) ?: return null
        return keys.unwrap(alias(accountId), WrappedSecret(decode(iv), decode(ciphertext)))
    }

    fun create(accountId: String): ByteArray {
        val passphrase = ByteArray(PASSPHRASE_BYTES).also(random::nextBytes)
        val wrapped = keys.wrap(alias(accountId), passphrase)
        prefs.edit()
            .putString("$accountId.iv", encode(wrapped.iv))
            .putString("$accountId.ct", encode(wrapped.ciphertext))
            .commit()
        return passphrase
    }

    fun delete(accountId: String) {
        prefs.edit().remove("$accountId.iv").remove("$accountId.ct").commit()
        keys.delete(alias(accountId))
    }

    private fun alias(accountId: String) = "solventa_wallet_$accountId"
    private fun encode(bytes: ByteArray) = Base64.getEncoder().encodeToString(bytes)
    private fun decode(value: String) = Base64.getDecoder().decode(value)

    companion object {
        private const val PREFS_NAME = "solventa_wallet"
        private const val PASSPHRASE_BYTES = 32

        /** Identificador de la cuenta para archivos y alias, sin dejar el correo en el teléfono. */
        fun accountId(email: String): String =
            MessageDigest.getInstance("SHA-256")
                .digest(email.trim().lowercase().toByteArray(Charsets.UTF_8))
                .joinToString("") { "%02x".format(it) }
                .take(32)
    }
}

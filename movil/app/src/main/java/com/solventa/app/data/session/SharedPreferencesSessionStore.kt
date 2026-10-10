package com.solventa.app.data.session

import android.content.Context
import java.util.Base64

// Solo guarda el texto cifrado por el Keystore; sin la llave no se puede leer.
class SharedPreferencesSessionStore(context: Context) : EncryptedSessionStore {

    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    override fun read(): EncryptedSession? {
        val ciphertext = prefs.getString(KEY_CIPHERTEXT, null) ?: return null
        val iv = prefs.getString(KEY_IV, null) ?: return null
        return EncryptedSession(decode(ciphertext), decode(iv))
    }

    override fun write(session: EncryptedSession) {
        prefs.edit()
            .putString(KEY_CIPHERTEXT, encode(session.ciphertext))
            .putString(KEY_IV, encode(session.iv))
            .commit()
    }

    override fun clear() {
        prefs.edit().clear().commit()
    }

    private fun encode(bytes: ByteArray) = Base64.getEncoder().encodeToString(bytes)
    private fun decode(value: String) = Base64.getDecoder().decode(value)

    private companion object {
        const val PREFS_NAME = "solventa_session"
        const val KEY_CIPHERTEXT = "ciphertext"
        const val KEY_IV = "iv"
    }
}

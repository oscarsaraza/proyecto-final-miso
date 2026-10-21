package com.solventa.app.data.session

import android.content.Context
import java.util.Base64

// Guarda el texto cifrado por el Keystore y el id público del dispositivo; sin la llave no se puede leer el secreto.
class SharedPreferencesSessionStore(context: Context) : EncryptedSessionStore {

    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    override fun read(): EncryptedSession? {
        val ciphertext = prefs.getString(KEY_CIPHERTEXT, null) ?: return null
        val iv = prefs.getString(KEY_IV, null) ?: return null
        return EncryptedSession(decode(ciphertext), decode(iv), prefs.getString(KEY_DEVICE_ID, null))
    }

    override fun write(session: EncryptedSession) {
        prefs.edit()
            .putString(KEY_CIPHERTEXT, encode(session.ciphertext))
            .putString(KEY_IV, encode(session.iv))
            .putString(KEY_DEVICE_ID, session.deviceId)
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
        const val KEY_DEVICE_ID = "device_id"
    }
}

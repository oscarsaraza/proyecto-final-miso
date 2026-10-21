package com.solventa.app.data.session

import android.content.Context
import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject
import java.util.Base64

// Guarda por cuenta el texto cifrado por el Keystore y sus datos públicos; sin la llave no se lee el secreto.
class SharedPreferencesSessionStore(context: Context) : EncryptedSessionStore {

    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    override fun readAll(): List<EncryptedSession> {
        val raw = prefs.getString(KEY_ACCOUNTS, null) ?: return emptyList()
        return try {
            val array = JSONArray(raw)
            (0 until array.length()).map { i ->
                val json = array.getJSONObject(i)
                EncryptedSession(
                    ciphertext = decode(json.getString("ciphertext")),
                    iv = decode(json.getString("iv")),
                    deviceId = json.getString("device_id"),
                    accountEmail = json.getString("email"),
                    accountName = json.getString("name"),
                )
            }
        } catch (e: JSONException) {
            emptyList()
        }
    }

    override fun write(session: EncryptedSession) {
        save(readAll().filterNot { it.accountEmail == session.accountEmail } + session)
    }

    override fun remove(accountEmail: String) {
        save(readAll().filterNot { it.accountEmail == accountEmail })
    }

    override fun clear() {
        prefs.edit().clear().commit()
    }

    private fun save(sessions: List<EncryptedSession>) {
        val array = JSONArray()
        sessions.forEach { session ->
            array.put(
                JSONObject()
                    .put("ciphertext", encode(session.ciphertext))
                    .put("iv", encode(session.iv))
                    .put("device_id", session.deviceId)
                    .put("email", session.accountEmail)
                    .put("name", session.accountName)
            )
        }
        prefs.edit().clear().putString(KEY_ACCOUNTS, array.toString()).commit()
    }

    private fun encode(bytes: ByteArray) = Base64.getEncoder().encodeToString(bytes)
    private fun decode(value: String) = Base64.getDecoder().decode(value)

    private companion object {
        const val PREFS_NAME = "solventa_session"
        const val KEY_ACCOUNTS = "accounts"
    }
}

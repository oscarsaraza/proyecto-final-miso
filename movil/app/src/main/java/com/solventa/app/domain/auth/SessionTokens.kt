package com.solventa.app.domain.auth

class SessionTokens(val accessToken: String, val refreshToken: String) {

    fun toBytes(): ByteArray = "$accessToken\n$refreshToken".toByteArray(Charsets.UTF_8)

    override fun equals(other: Any?): Boolean =
        other is SessionTokens && other.accessToken == accessToken && other.refreshToken == refreshToken

    override fun hashCode(): Int = 31 * accessToken.hashCode() + refreshToken.hashCode()

    override fun toString(): String = "SessionTokens(***)"

    companion object {
        fun fromBytes(bytes: ByteArray): SessionTokens {
            val parts = String(bytes, Charsets.UTF_8).split('\n')
            require(parts.size == 2) { "Formato de sesión inválido" }
            return SessionTokens(parts[0], parts[1])
        }
    }
}

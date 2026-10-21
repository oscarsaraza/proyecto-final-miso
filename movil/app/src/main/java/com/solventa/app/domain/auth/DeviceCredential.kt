package com.solventa.app.domain.auth

/** Credencial del teléfono vinculado para entrar con huella; se guarda cifrada con la llave biométrica. */
class DeviceCredential(val deviceId: String, val secret: String) {

    fun toBytes(): ByteArray = "$deviceId\n$secret".toByteArray(Charsets.UTF_8)

    override fun equals(other: Any?): Boolean =
        other is DeviceCredential && other.deviceId == deviceId && other.secret == secret

    override fun hashCode(): Int = 31 * deviceId.hashCode() + secret.hashCode()

    override fun toString(): String = "DeviceCredential($deviceId, ***)"

    companion object {
        fun fromBytes(bytes: ByteArray): DeviceCredential {
            val parts = String(bytes, Charsets.UTF_8).split('\n')
            require(parts.size == 2) { "Formato de credencial inválido" }
            return DeviceCredential(parts[0], parts[1])
        }
    }
}

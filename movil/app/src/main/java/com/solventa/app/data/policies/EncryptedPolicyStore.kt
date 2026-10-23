package com.solventa.app.data.policies

import android.content.Context
import androidx.room.Room
import com.solventa.app.domain.policies.CoverageLimit
import com.solventa.app.domain.policies.PolicyCard
import com.solventa.app.domain.policies.PolicyStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import net.zetetic.database.sqlcipher.SupportOpenHelperFactory
import org.json.JSONArray
import org.json.JSONObject
import java.time.Clock
import java.time.Instant

/**
 * Copia de la billetera en una base SQLCipher por cuenta (HU-MOV-04, CTL-03). La frase solo existe en
 * claro mientras dura cada operación; si la base o la llave ya no sirven, la copia se borra.
 */
class EncryptedPolicyStore(
    private val context: Context,
    private val vault: PassphraseVault,
    private val clock: Clock = Clock.systemUTC(),
) : PolicyStore {

    override suspend fun save(accountEmail: String, policies: List<PolicyCard>) = withContext(Dispatchers.IO) {
        val accountId = PassphraseVault.accountId(accountEmail)
        val passphrase = vault.existing(accountId) ?: run {
            discard(accountId)
            vault.create(accountId)
        }
        withDatabase(accountId, passphrase) { db ->
            db.policyCards().replace(policies.map(PolicyCard::toEntity), clock.millis())
        }
    }

    override suspend fun read(accountEmail: String): List<PolicyCard>? = withContext(Dispatchers.IO) {
        val accountId = PassphraseVault.accountId(accountEmail)
        if (!context.getDatabasePath(fileName(accountId)).exists()) return@withContext null
        val passphrase = vault.existing(accountId) ?: run {
            discard(accountId)
            return@withContext null
        }
        try {
            withDatabase(accountId, passphrase) { db ->
                if (db.policyCards().hasCopy() == 0) null else db.policyCards().all().map(PolicyCardEntity::toCard)
            }
        } catch (e: RuntimeException) {
            discard(accountId)
            null
        }
    }

    override suspend fun delete(accountEmail: String) = withContext(Dispatchers.IO) {
        discard(PassphraseVault.accountId(accountEmail))
    }

    private fun discard(accountId: String) {
        context.deleteDatabase(fileName(accountId))
        vault.delete(accountId)
    }

    private suspend fun <T> withDatabase(accountId: String, passphrase: ByteArray, block: suspend (WalletDatabase) -> T): T {
        sqlcipherLoaded
        val db = Room.databaseBuilder(context, WalletDatabase::class.java, fileName(accountId))
            .openHelperFactory(SupportOpenHelperFactory(passphrase))
            .build()
        try {
            return block(db)
        } finally {
            db.close()
            passphrase.fill(0)
        }
    }

    private fun fileName(accountId: String) = "wallet_$accountId.db"

    private companion object {
        val sqlcipherLoaded: Unit by lazy { System.loadLibrary("sqlcipher") }
    }
}

internal fun PolicyCard.toEntity() = PolicyCardEntity(
    policyNumber = policyNumber,
    plan = plan,
    holderName = holderName,
    coveragesJson = JSONArray(coverages.map { JSONObject().put("name", it.name).put("limit", it.limit) }).toString(),
    validFromEpochMillis = validFrom.toEpochMilli(),
    validUntilEpochMillis = validUntil.toEpochMilli(),
)

internal fun PolicyCardEntity.toCard(): PolicyCard {
    val coverages = JSONArray(coveragesJson)
    return PolicyCard(
        policyNumber = policyNumber,
        plan = plan,
        holderName = holderName,
        coverages = (0 until coverages.length()).map { i ->
            val coverage = coverages.getJSONObject(i)
            CoverageLimit(coverage.getString("name"), coverage.getDouble("limit"))
        },
        validFrom = Instant.ofEpochMilli(validFromEpochMillis),
        validUntil = Instant.ofEpochMilli(validUntilEpochMillis),
    )
}

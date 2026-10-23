package com.solventa.app.data.policies

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase
import androidx.room.Transaction

@Entity(tableName = "policy_cards")
data class PolicyCardEntity(
    @PrimaryKey val policyNumber: String,
    val plan: String,
    val holderName: String,
    val coveragesJson: String,
    val validFromEpochMillis: Long,
    val validUntilEpochMillis: Long,
)

@Entity(tableName = "wallet_meta")
data class WalletMetaEntity(
    @PrimaryKey val id: Int = 0,
    val savedAtEpochMillis: Long,
)

@Dao
interface PolicyCardDao {
    @Query("SELECT * FROM policy_cards ORDER BY validUntilEpochMillis")
    suspend fun all(): List<PolicyCardEntity>

    @Query("SELECT COUNT(*) FROM wallet_meta")
    suspend fun hasCopy(): Int

    @Transaction
    suspend fun replace(cards: List<PolicyCardEntity>, savedAtEpochMillis: Long) {
        deleteCards()
        insertCards(cards)
        saveMeta(WalletMetaEntity(savedAtEpochMillis = savedAtEpochMillis))
    }

    @Query("DELETE FROM policy_cards")
    suspend fun deleteCards()

    @Insert
    suspend fun insertCards(cards: List<PolicyCardEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun saveMeta(meta: WalletMetaEntity)
}

@Database(entities = [PolicyCardEntity::class, WalletMetaEntity::class], version = 1, exportSchema = false)
abstract class WalletDatabase : RoomDatabase() {
    abstract fun policyCards(): PolicyCardDao
}

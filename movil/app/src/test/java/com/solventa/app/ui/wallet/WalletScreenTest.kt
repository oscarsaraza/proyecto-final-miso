package com.solventa.app.ui.wallet

import android.content.Context
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.test.core.app.ApplicationProvider
import com.solventa.app.R
import com.solventa.app.data.policies.samplePolicy
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

// Estados de la billetera y su lectura con TalkBack (HU-MOV-04: TC-04, TC-05, TC-09).
@RunWith(RobolectricTestRunner::class)
class WalletScreenTest {

    @get:Rule
    val compose = createComposeRule()

    private val context: Context = ApplicationProvider.getApplicationContext()

    private fun s(id: Int, vararg args: Any): String = context.getString(id, *args)

    private fun show(state: WalletUiState, biometricEnabled: Boolean = true) {
        compose.setContent {
            WalletScreen(
                uiState = state,
                fullName = "María Ruiz",
                biometricEnabled = biometricEnabled,
                onDisableBiometrics = {},
                onLogout = {},
            )
        }
    }

    @Test
    fun `con red muestra cada poliza como una tarjeta que se lee completa`() {
        show(WalletUiState(loading = false, policies = listOf(WalletCard(samplePolicy(), expired = false))))

        compose.onNode(SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading))
            .assertIsDisplayed()
        compose.onNodeWithText(s(R.string.wallet_policy_number, "POL-2026-00001"), substring = true, useUnmergedTree = false)
            .assertIsDisplayed()
        compose.onNodeWithText(s(R.string.wallet_plan, s(R.string.wallet_plan_premium)), substring = true)
            .assertIsDisplayed()
        compose.onNodeWithText(s(R.string.wallet_holder, "María Ruiz"), substring = true).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.wallet_offline)).assertDoesNotExist()
        compose.onNodeWithText(s(R.string.biometric_disable)).assertIsDisplayed()
    }

    @Test
    fun `sin red muestra el aviso, la copia y una poliza vencida`() {
        show(
            WalletUiState(
                loading = false,
                offline = true,
                policies = listOf(WalletCard(samplePolicy(), expired = true)),
            )
        )

        compose.onNodeWithText(s(R.string.wallet_offline)).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.wallet_expired), substring = true).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.biometric_disable)).assertDoesNotExist()
    }

    @Test
    fun `sin red y sin copia pide conexion para la primera descarga`() {
        show(WalletUiState(loading = false, offline = true, needsConnection = true))

        compose.onNodeWithText(s(R.string.wallet_needs_connection)).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.wallet_offline)).assertDoesNotExist()
    }

    @Test
    fun `sin polizas vigentes lo indica`() {
        show(WalletUiState(loading = false))

        compose.onNodeWithText(s(R.string.wallet_empty)).assertIsDisplayed()
    }

    @Test
    fun `mientras carga anuncia la carga`() {
        show(WalletUiState())

        compose.onNodeWithContentDescription(s(R.string.wallet_loading)).assertIsDisplayed()
    }
}

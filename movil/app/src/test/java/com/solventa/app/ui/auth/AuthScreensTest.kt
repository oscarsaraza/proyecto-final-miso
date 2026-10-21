package com.solventa.app.ui.auth

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import com.solventa.app.R
import com.solventa.app.data.session.BoundAccount
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class AuthScreensTest {

    @get:Rule
    val compose = createComposeRule()

    private val context: Context = ApplicationProvider.getApplicationContext()

    private fun s(id: Int, vararg args: Any): String = context.getString(id, *args)

    private val maria = BoundAccount("maria.ruiz@correo.co", "María Ruiz")
    private val pedro = BoundAccount("pedro.gomez@correo.co", "Pedro Gómez")

    // Pantalla de huella

    @Test
    fun `huella sin cuentas invita a tocar el sensor y no ofrece cambiar de usuario`() {
        var authenticated = 0
        var alternative = 0
        compose.setContent {
            BiometricLoginScreen(AuthUiState(), onAuthenticate = { authenticated++ }, onUseAlternative = { alternative++ })
        }

        compose.onNodeWithText(s(R.string.auth_biometric_subtitle)).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.auth_switch_user)).assertDoesNotExist()
        compose.onNodeWithContentDescription(s(R.string.auth_sensor_description)).performClick()
        compose.onNodeWithText(s(R.string.auth_use_alternative)).performClick()

        assertEquals(1, authenticated)
        assertEquals(1, alternative)
    }

    @Test
    fun `huella con una cuenta muestra su nombre y permite cambiar de usuario`() {
        var switched = 0
        compose.setContent {
            BiometricLoginScreen(
                AuthUiState(biometricAccounts = listOf(maria), selectedAccountEmail = maria.email),
                onAuthenticate = {},
                onUseAlternative = {},
                onSwitchUser = { switched++ },
            )
        }

        compose.onNodeWithText(s(R.string.auth_biometric_account, "María Ruiz")).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.auth_switch_user)).performClick()

        assertEquals(1, switched)
    }

    @Test
    fun `huella con varias cuentas deja elegir con cual entrar`() {
        val selected = mutableListOf<String>()
        compose.setContent {
            BiometricLoginScreen(
                AuthUiState(biometricAccounts = listOf(maria, pedro), selectedAccountEmail = pedro.email),
                onAuthenticate = {},
                onUseAlternative = {},
                onSelectAccount = { selected += it },
            )
        }

        compose.onNodeWithText(s(R.string.auth_biometric_account, "Pedro Gómez")).assertIsDisplayed()
        compose.onNodeWithText("María Ruiz").performClick()

        assertEquals(listOf(maria.email), selected)
    }

    @Test
    fun `cada estado de la huella muestra su mensaje y bloquea el sensor cuando corresponde`() {
        var status by mutableStateOf(AuthStatus.IDLE)
        compose.setContent {
            BiometricLoginScreen(AuthUiState(status = status), onAuthenticate = {}, onUseAlternative = {})
        }
        val messages = mapOf(
            AuthStatus.IDLE to R.string.auth_status_idle,
            AuthStatus.AUTHENTICATING to R.string.auth_status_authenticating,
            AuthStatus.AUTHENTICATED to R.string.auth_status_authenticated,
            AuthStatus.CANCELLED to R.string.auth_status_cancelled,
            AuthStatus.BIOMETRIC_UNAVAILABLE to R.string.auth_status_unavailable,
            AuthStatus.BIOMETRIC_NOT_ENROLLED to R.string.auth_status_not_enrolled,
            AuthStatus.BIOMETRIC_LOCKED_OUT to R.string.auth_status_locked_out,
            AuthStatus.BIOMETRIC_ERROR to R.string.auth_status_error,
            AuthStatus.NO_STORED_SESSION to R.string.auth_status_no_session,
            AuthStatus.SESSION_RESET to R.string.auth_status_session_reset,
            AuthStatus.LOGGED_OUT to R.string.auth_status_logged_out,
            AuthStatus.LOGGED_OUT_BIOMETRIC_READY to R.string.auth_status_logged_out_biometric,
            AuthStatus.ACCOUNT_LOCKED to R.string.auth_status_account_locked,
            AuthStatus.SERVER_UNREACHABLE to R.string.auth_status_server_unreachable,
        )
        assertEquals(AuthStatus.entries.size, messages.size)

        messages.forEach { (value, message) ->
            status = value
            compose.onNodeWithText(s(message)).assertIsDisplayed()
        }
        status = AuthStatus.LOGGED_OUT
        compose.onNodeWithContentDescription(s(R.string.auth_sensor_description)).assertIsNotEnabled()
    }

    // Acceso con contraseña y código

    @Test
    fun `acceso alterno pide el codigo, ingresa y abre la recuperacion`() {
        val otpRequests = mutableListOf<String>()
        val submits = mutableListOf<Triple<String, String, String>>()
        var forgot = 0
        var back = 0
        compose.setContent {
            AlternativeLoginScreen(
                uiState = AuthUiState(prefillEmail = maria.email),
                onRequestOtp = { otpRequests += it },
                onSubmit = { email, password, code -> submits += Triple(email, password, code) },
                onBack = { back++ },
                onForgotPassword = { forgot++ },
            )
        }

        compose.onNodeWithText(s(R.string.auth_submit)).assertIsNotEnabled()
        compose.onNodeWithText(s(R.string.auth_otp_send)).performClick()
        compose.onNodeWithText(s(R.string.auth_password)).performTextInput("Solventa2026!")
        compose.onNodeWithText(s(R.string.auth_otp)).performTextInput("41a7902x")
        compose.onNodeWithText(s(R.string.auth_submit)).assertIsEnabled().performClick()
        compose.onNodeWithText(s(R.string.auth_forgot_password)).performScrollTo().performClick()
        compose.onNodeWithText(s(R.string.auth_back_to_biometrics)).performScrollTo().performClick()

        assertEquals(listOf(maria.email), otpRequests)
        assertEquals(listOf(Triple(maria.email, "Solventa2026!", "417902")), submits)
        assertEquals(1, forgot)
        assertEquals(1, back)
    }

    @Test
    fun `acceso alterno muestra codigo de prueba, espera para reenviar y cuenta regresiva`() {
        var state by mutableStateOf(
            AuthUiState(
                prefillEmail = maria.email,
                otpCooldownSeconds = 42,
                otpCooldownEmail = maria.email,
                lockedSeconds = 125,
                alternativeLogin = AlternativeLoginState(otpSent = true, debugOtpCode = "417902"),
            )
        )
        compose.setContent {
            AlternativeLoginScreen(state, onRequestOtp = {}, onSubmit = { _, _, _ -> }, onBack = {}, onForgotPassword = {})
        }

        compose.onNodeWithText(s(R.string.auth_otp_wait, 42)).assertIsNotEnabled()
        compose.onNodeWithText(s(R.string.auth_otp_sent_debug, "417902")).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.auth_locked_countdown, 2, 5)).assertIsDisplayed()

        state = state.copy(otpCooldownSeconds = 0, lockedSeconds = 0, alternativeLogin = AlternativeLoginState(otpSent = true))
        compose.onNodeWithText(s(R.string.auth_otp_resend)).assertIsEnabled()
        compose.onNodeWithText(s(R.string.auth_otp_sent)).assertIsDisplayed()
    }

    @Test
    fun `acceso alterno muestra cada error`() {
        var error by mutableStateOf(AlternativeLoginError.INVALID_CREDENTIALS)
        compose.setContent {
            AlternativeLoginScreen(
                AuthUiState(alternativeLogin = AlternativeLoginState(error = error)),
                onRequestOtp = {},
                onSubmit = { _, _, _ -> },
                onBack = {},
                onForgotPassword = {},
            )
        }
        val messages = mapOf(
            AlternativeLoginError.INVALID_CREDENTIALS to R.string.auth_error_invalid_credentials,
            AlternativeLoginError.INVALID_FORMAT to R.string.auth_error_invalid_format,
            AlternativeLoginError.ACCOUNT_LOCKED to R.string.auth_error_locked,
            AlternativeLoginError.TOO_MANY_REQUESTS to R.string.auth_error_too_many,
            AlternativeLoginError.SMS_UNAVAILABLE to R.string.auth_error_sms,
            AlternativeLoginError.NETWORK to R.string.auth_error_network,
        )
        assertEquals(AlternativeLoginError.entries.size, messages.size)

        messages.forEach { (value, message) ->
            error = value
            compose.onNodeWithText(s(message)).assertIsDisplayed()
        }
    }

    @Test
    fun `mientras se verifica el boton de ingresar queda deshabilitado`() {
        compose.setContent {
            AlternativeLoginScreen(
                AuthUiState(alternativeLogin = AlternativeLoginState(isSubmitting = true)),
                onRequestOtp = {},
                onSubmit = { _, _, _ -> },
                onBack = {},
                onForgotPassword = {},
            )
        }

        compose.onNodeWithText(s(R.string.auth_submitting)).assertIsNotEnabled()
    }

    // Diálogos

    @Test
    fun `dialogo de activar la huella`() {
        var enabled = 0
        var skipped = 0
        compose.setContent { BiometricEnrollmentDialog(onEnable = { enabled++ }, onSkip = { skipped++ }) }

        compose.onNodeWithText(s(R.string.auth_enroll_message)).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.auth_enroll_confirm)).performClick()
        compose.onNodeWithText(s(R.string.auth_enroll_skip)).performClick()

        assertEquals(1, enabled)
        assertEquals(1, skipped)
    }

    @Test
    fun `dialogo de cerrar sesion avisa si la huella sigue activa`() {
        var biometric by mutableStateOf(true)
        var confirmed = 0
        var dismissed = 0
        compose.setContent {
            LogoutConfirmationDialog(biometricEnabled = biometric, onConfirm = { confirmed++ }, onDismiss = { dismissed++ })
        }

        compose.onNodeWithText(s(R.string.logout_message_biometric)).assertIsDisplayed()
        biometric = false
        compose.onNodeWithText(s(R.string.logout_message)).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.logout_confirm)).performClick()
        compose.onNodeWithText(s(R.string.logout_cancel)).performClick()

        assertEquals(1, confirmed)
        assertEquals(1, dismissed)
    }

    // Recuperación de contraseña

    @Test
    fun `recuperacion marca los requisitos en cada campo y envia solo cuando se cumplen`() {
        val codes = mutableListOf<String>()
        val submits = mutableListOf<List<String>>()
        var closed = 0
        compose.setContent {
            PasswordRecoveryScreen(
                uiState = AuthUiState(recovery = PasswordRecoveryState(codeSent = true, debugCode = "123456")),
                onRequestCode = { codes += it },
                onSubmit = { email, code, password, confirmation -> submits += listOf(email, code, password, confirmation) },
                onClose = { closed++ },
            )
        }

        compose.onNodeWithText(s(R.string.auth_otp_sent_debug, "123456")).assertIsDisplayed()
        compose.onNodeWithText(s(R.string.auth_email)).performTextInput(maria.email)
        compose.onNodeWithText(s(R.string.recovery_send)).performClick()
        compose.onNodeWithText(s(R.string.recovery_code)).performTextInput("123456")
        compose.onNodeWithContentDescription("${s(R.string.recovery_rule_length)}: ${s(R.string.recovery_rule_pending)}")
            .assertExists()

        compose.onNodeWithText(s(R.string.recovery_new_password)).performTextInput("NuevaClave2026")
        compose.onNodeWithContentDescription("${s(R.string.recovery_rule_length)}: ${s(R.string.recovery_rule_met)}")
            .assertExists()
        compose.onNodeWithContentDescription("${s(R.string.recovery_rule_mix)}: ${s(R.string.recovery_rule_met)}")
            .assertExists()
        compose.onNodeWithText(s(R.string.recovery_submit)).performScrollTo().assertIsNotEnabled()

        compose.onNodeWithText(s(R.string.recovery_confirm_password)).performTextInput("NuevaClave2026")
        compose.onNodeWithContentDescription("${s(R.string.recovery_rule_match)}: ${s(R.string.recovery_rule_met)}")
            .assertExists()
        compose.onNodeWithText(s(R.string.recovery_submit)).performScrollTo().assertIsEnabled().performClick()
        compose.onNodeWithText(s(R.string.recovery_back)).performScrollTo().performClick()

        assertEquals(listOf(maria.email), codes)
        assertEquals(listOf(listOf(maria.email, "123456", "NuevaClave2026", "NuevaClave2026")), submits)
        assertEquals(1, closed)
    }

    @Test
    fun `recuperacion muestra cada error, la espera para reenviar y el exito`() {
        var state by mutableStateOf(
            AuthUiState(otpCooldownSeconds = 30, recovery = PasswordRecoveryState(codeSent = true, error = RecoveryError.INVALID_CODE))
        )
        compose.setContent {
            PasswordRecoveryScreen(state, onRequestCode = {}, onSubmit = { _, _, _, _ -> }, onClose = {})
        }
        compose.onNodeWithText(s(R.string.auth_otp_sent)).assertIsDisplayed()
        val messages = mapOf(
            RecoveryError.INVALID_CODE to R.string.recovery_error_code,
            RecoveryError.WEAK_PASSWORD to R.string.recovery_error_weak,
            RecoveryError.SAME_PASSWORD to R.string.recovery_error_same,
            RecoveryError.PASSWORD_MISMATCH to R.string.recovery_error_mismatch,
            RecoveryError.TOO_MANY_REQUESTS to R.string.auth_error_too_many,
            RecoveryError.SMS_UNAVAILABLE to R.string.auth_error_sms,
            RecoveryError.NETWORK to R.string.auth_error_network,
        )
        assertEquals(RecoveryError.entries.size, messages.size)
        messages.forEach { (value, message) ->
            state = state.copy(recovery = state.recovery.copy(error = value))
            compose.onNodeWithText(s(message)).performScrollTo().assertIsDisplayed()
        }

        compose.onNodeWithText(s(R.string.auth_email)).performTextInput(maria.email)
        state = state.copy(otpCooldownEmail = maria.email)
        compose.onNodeWithText(s(R.string.auth_otp_wait, 30)).assertIsNotEnabled()

        state = state.copy(recovery = PasswordRecoveryState(isSubmitting = true))
        compose.onNodeWithText(s(R.string.auth_submitting)).performScrollTo().assertIsNotEnabled()

        state = state.copy(recovery = PasswordRecoveryState(completed = true))
        compose.onNodeWithText(s(R.string.recovery_done)).assertIsDisplayed()
    }

    @Test
    fun `reglas de la contrasena`() {
        assertTrue(meetsLength("12345678"))
        assertTrue(mixesLettersAndDigits("abc123"))
    }
}

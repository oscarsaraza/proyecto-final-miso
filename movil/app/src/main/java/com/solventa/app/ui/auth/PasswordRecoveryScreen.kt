package com.solventa.app.ui.auth

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.solventa.app.R
import com.solventa.app.ui.theme.SolventaTheme

private const val CODE_LENGTH = 6

@Composable
fun PasswordRecoveryScreen(
    uiState: AuthUiState,
    onRequestCode: (email: String) -> Unit,
    onSubmit: (email: String, code: String, newPassword: String, confirmation: String) -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
) {
    BackHandler(onBack = onClose)
    var email by rememberSaveable { mutableStateOf("") }
    var code by rememberSaveable { mutableStateOf("") }
    var newPassword by rememberSaveable { mutableStateOf("") }
    var confirmation by rememberSaveable { mutableStateOf("") }
    val recovery = uiState.recovery

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            text = stringResource(R.string.recovery_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )

        if (recovery.completed) {
            Text(text = stringResource(R.string.recovery_done))
            Spacer(Modifier.height(8.dp))
            Button(onClick = onClose, modifier = Modifier.fillMaxWidth().height(48.dp)) {
                Text(stringResource(R.string.recovery_back))
            }
            return@Column
        }

        Text(
            text = stringResource(R.string.recovery_subtitle),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text(stringResource(R.string.auth_email)) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                modifier = Modifier.weight(1f),
            )
            OutlinedButton(
                onClick = { onRequestCode(email) },
                enabled = email.isNotBlank() && uiState.canRequestOtp(email),
            ) {
                Text(
                    if (!uiState.canRequestOtp(email)) {
                        stringResource(R.string.auth_otp_wait, uiState.otpCooldownSeconds)
                    } else {
                        stringResource(R.string.recovery_send)
                    }
                )
            }
        }
        if (recovery.codeSent) {
            Text(
                text = recovery.debugCode?.let { stringResource(R.string.auth_otp_sent_debug, it) }
                    ?: stringResource(R.string.auth_otp_sent),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        OutlinedTextField(
            value = code,
            onValueChange = { value -> code = value.filter(Char::isDigit).take(CODE_LENGTH) },
            label = { Text(stringResource(R.string.recovery_code)) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
            modifier = Modifier.fillMaxWidth(),
        )
        PasswordField(
            value = newPassword,
            onValueChange = { newPassword = it },
            label = stringResource(R.string.recovery_new_password),
            modifier = Modifier.fillMaxWidth(),
        )
        NewPasswordRequirements(newPassword = newPassword)
        PasswordField(
            value = confirmation,
            onValueChange = { confirmation = it },
            label = stringResource(R.string.recovery_confirm_password),
            modifier = Modifier.fillMaxWidth(),
        )
        MatchRequirement(newPassword = newPassword, confirmation = confirmation)

        recovery.error?.let { error ->
            Text(
                text = when (error) {
                    RecoveryError.INVALID_CODE -> stringResource(R.string.recovery_error_code)
                    RecoveryError.WEAK_PASSWORD -> stringResource(R.string.recovery_error_weak)
                    RecoveryError.SAME_PASSWORD -> stringResource(R.string.recovery_error_same)
                    RecoveryError.PASSWORD_MISMATCH -> stringResource(R.string.recovery_error_mismatch)
                    RecoveryError.TOO_MANY_REQUESTS -> stringResource(R.string.auth_error_too_many)
                    RecoveryError.SMS_UNAVAILABLE -> stringResource(R.string.auth_error_sms)
                    RecoveryError.NETWORK -> stringResource(R.string.auth_error_network)
                },
                color = MaterialTheme.colorScheme.error,
                fontWeight = FontWeight.SemiBold,
            )
        }

        Spacer(Modifier.height(8.dp))
        Button(
            onClick = { onSubmit(email, code, newPassword, confirmation) },
            enabled = email.isNotBlank() && code.length == CODE_LENGTH &&
                passwordRulesMet(newPassword, confirmation) && !recovery.isSubmitting,
            modifier = Modifier.fillMaxWidth().height(48.dp),
        ) {
            Text(stringResource(if (recovery.isSubmitting) R.string.auth_submitting else R.string.recovery_submit))
        }
        OutlinedButton(onClick = onClose, modifier = Modifier.fillMaxWidth().height(48.dp)) {
            Text(stringResource(R.string.recovery_back))
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun PasswordRecoveryScreenPreview() {
    SolventaTheme {
        PasswordRecoveryScreen(
            uiState = AuthUiState(recovery = PasswordRecoveryState(codeSent = true, debugCode = "417902")),
            onRequestCode = {},
            onSubmit = { _, _, _, _ -> },
            onClose = {},
        )
    }
}

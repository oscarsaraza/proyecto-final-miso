package com.solventa.app.ui.auth

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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.solventa.app.R
import com.solventa.app.ui.theme.SolventaTheme

private const val OTP_LENGTH = 6

@Composable
fun AlternativeLoginScreen(
    uiState: AuthUiState,
    onRequestOtp: (email: String) -> Unit,
    onSubmit: (email: String, password: String, otpCode: String) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var email by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var otpCode by rememberSaveable { mutableStateOf("") }
    val form = uiState.alternativeLogin
    val canSubmit = email.isNotBlank() && password.isNotBlank() && otpCode.length == OTP_LENGTH &&
        !form.isSubmitting && !uiState.isLocked

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            text = stringResource(R.string.auth_alternative_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = stringResource(R.string.auth_alternative_subtitle),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text(stringResource(R.string.auth_email)) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text(stringResource(R.string.auth_password)) },
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            modifier = Modifier.fillMaxWidth(),
        )
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = otpCode,
                onValueChange = { value -> otpCode = value.filter(Char::isDigit).take(OTP_LENGTH) },
                label = { Text(stringResource(R.string.auth_otp)) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                modifier = Modifier.weight(1f),
            )
            OutlinedButton(onClick = { onRequestOtp(email) }, enabled = email.isNotBlank()) {
                Text(stringResource(if (form.otpSent) R.string.auth_otp_resend else R.string.auth_otp_send))
            }
        }
        if (form.otpSent) {
            Text(
                text = form.debugOtpCode?.let { stringResource(R.string.auth_otp_sent_debug, it) }
                    ?: stringResource(R.string.auth_otp_sent),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        form.error?.let { error ->
            Text(
                text = when (error) {
                    AlternativeLoginError.INVALID_CREDENTIALS -> stringResource(R.string.auth_error_invalid_credentials)
                    AlternativeLoginError.ACCOUNT_LOCKED -> stringResource(R.string.auth_error_locked)
                    AlternativeLoginError.NETWORK -> stringResource(R.string.auth_error_network)
                },
                color = MaterialTheme.colorScheme.error,
                fontWeight = FontWeight.SemiBold,
            )
        }

        Spacer(Modifier.height(8.dp))
        Button(
            onClick = { onSubmit(email, password, otpCode) },
            enabled = canSubmit,
            modifier = Modifier.fillMaxWidth().height(48.dp),
        ) {
            Text(stringResource(if (form.isSubmitting) R.string.auth_submitting else R.string.auth_submit))
        }
        OutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth().height(48.dp)) {
            Text(stringResource(R.string.auth_back_to_biometrics))
        }
    }
}

@Composable
fun BiometricEnrollmentDialog(onEnable: () -> Unit, onSkip: () -> Unit) {
    AlertDialog(
        onDismissRequest = onSkip,
        title = { Text(stringResource(R.string.auth_enroll_title)) },
        text = { Text(stringResource(R.string.auth_enroll_message)) },
        confirmButton = { TextButton(onClick = onEnable) { Text(stringResource(R.string.auth_enroll_confirm)) } },
        dismissButton = { TextButton(onClick = onSkip) { Text(stringResource(R.string.auth_enroll_skip)) } },
    )
}

@Preview(showBackground = true)
@Composable
private fun AlternativeLoginScreenPreview() {
    SolventaTheme {
        AlternativeLoginScreen(
            uiState = AuthUiState(
                failedAttempts = 1,
                alternativeLogin = AlternativeLoginState(
                    otpSent = true,
                    debugOtpCode = "417902",
                    error = AlternativeLoginError.INVALID_CREDENTIALS,
                ),
            ),
            onRequestOtp = {},
            onSubmit = { _, _, _ -> },
            onBack = {},
        )
    }
}

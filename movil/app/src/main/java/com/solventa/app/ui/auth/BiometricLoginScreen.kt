package com.solventa.app.ui.auth

import androidx.annotation.StringRes
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.solventa.app.R
import com.solventa.app.ui.theme.SolventaTheme

@Composable
fun BiometricLoginScreen(
    uiState: AuthUiState,
    onAuthenticate: () -> Unit,
    onUseAlternative: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val biometricBlocked = uiState.status in BLOCKING_STATUSES

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(
            modifier = Modifier
                .size(52.dp)
                .clip(RoundedCornerShape(15.dp))
                .background(
                    Brush.linearGradient(listOf(MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.secondary))
                ),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                painter = painterResource(R.drawable.ic_shield),
                contentDescription = null,
                tint = Color.White,
                modifier = Modifier.size(28.dp),
            )
        }
        Spacer(Modifier.height(16.dp))
        Text(
            text = stringResource(R.string.auth_biometric_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = stringResource(R.string.auth_biometric_subtitle),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            SensorButton(
                active = uiState.status == AuthStatus.AUTHENTICATING,
                enabled = !biometricBlocked,
                onClick = onAuthenticate,
            )
            Spacer(Modifier.height(20.dp))
            Text(
                text = stringResource(uiState.status.messageRes()),
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                textAlign = TextAlign.Center,
                color = if (biometricBlocked || uiState.status == AuthStatus.BIOMETRIC_ERROR) {
                    MaterialTheme.colorScheme.error
                } else {
                    MaterialTheme.colorScheme.primary
                },
            )
        }

        if (biometricBlocked) {
            Button(onClick = onUseAlternative, modifier = Modifier.fillMaxWidth().height(48.dp)) {
                Text(stringResource(R.string.auth_use_alternative))
            }
        } else {
            OutlinedButton(onClick = onUseAlternative, modifier = Modifier.fillMaxWidth().height(48.dp)) {
                Text(stringResource(R.string.auth_use_alternative))
            }
        }
    }
}

@Composable
private fun SensorButton(active: Boolean, enabled: Boolean, onClick: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = CircleShape,
        color = if (active) colors.primary else colors.primaryContainer,
        contentColor = if (active) colors.onPrimary else colors.primary,
        border = BorderStroke(2.dp, if (enabled) colors.primary else colors.outline),
        modifier = Modifier.size(104.dp),
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                painter = painterResource(R.drawable.ic_fingerprint),
                contentDescription = stringResource(R.string.auth_sensor_description),
                modifier = Modifier.size(56.dp),
            )
        }
    }
}

private val BLOCKING_STATUSES = setOf(
    AuthStatus.BIOMETRIC_UNAVAILABLE,
    AuthStatus.BIOMETRIC_NOT_ENROLLED,
    AuthStatus.BIOMETRIC_LOCKED_OUT,
)

@StringRes
private fun AuthStatus.messageRes(): Int = when (this) {
    AuthStatus.IDLE -> R.string.auth_status_idle
    AuthStatus.AUTHENTICATING -> R.string.auth_status_authenticating
    AuthStatus.AUTHENTICATED -> R.string.auth_status_authenticated
    AuthStatus.CANCELLED -> R.string.auth_status_cancelled
    AuthStatus.BIOMETRIC_UNAVAILABLE -> R.string.auth_status_unavailable
    AuthStatus.BIOMETRIC_NOT_ENROLLED -> R.string.auth_status_not_enrolled
    AuthStatus.BIOMETRIC_LOCKED_OUT -> R.string.auth_status_locked_out
    AuthStatus.BIOMETRIC_ERROR -> R.string.auth_status_error
}

@Preview(showBackground = true)
@Composable
private fun BiometricLoginScreenPreview() {
    SolventaTheme {
        BiometricLoginScreen(uiState = AuthUiState(), onAuthenticate = {}, onUseAlternative = {})
    }
}

@Preview(showBackground = true)
@Composable
private fun BiometricLoginScreenLockedPreview() {
    SolventaTheme {
        BiometricLoginScreen(
            uiState = AuthUiState(status = AuthStatus.BIOMETRIC_LOCKED_OUT),
            onAuthenticate = {},
            onUseAlternative = {},
        )
    }
}

package com.solventa.app.ui.wallet

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.solventa.app.R
import com.solventa.app.domain.policies.CoverageLimit
import com.solventa.app.domain.policies.PolicyCard
import com.solventa.app.ui.theme.SolventaTheme
import java.text.NumberFormat
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

private val COLOMBIA = Locale.forLanguageTag("es-CO")
private val DATE_FORMAT = DateTimeFormatter.ofPattern("d MMM yyyy", COLOMBIA)

@Composable
fun WalletScreen(
    uiState: WalletUiState,
    fullName: String?,
    biometricEnabled: Boolean,
    onDisableBiometrics: () -> Unit,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier,
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text(
                text = stringResource(R.string.wallet_title),
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.semantics { heading() },
            )
            fullName?.let {
                Text(
                    text = stringResource(R.string.home_title_named, it),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        if (uiState.offline && !uiState.needsConnection) {
            item { Notice(R.string.wallet_offline) }
        }
        when {
            uiState.loading -> item { Loading() }
            uiState.needsConnection -> item { Notice(R.string.wallet_needs_connection) }
            uiState.empty -> item { Message(R.string.wallet_empty) }
            else -> items(uiState.policies, key = { it.policy.policyNumber }) { PolicyCardView(it) }
        }
        item {
            Spacer(Modifier.height(12.dp))
            Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                OutlinedButton(onClick = onLogout, modifier = Modifier.heightIn(min = 48.dp)) {
                    Text(stringResource(R.string.logout_button))
                }
                if (biometricEnabled && !uiState.offline) {
                    TextButton(onClick = onDisableBiometrics, modifier = Modifier.heightIn(min = 48.dp)) {
                        Text(stringResource(R.string.biometric_disable))
                    }
                } else if (!biometricEnabled) {
                    Text(
                        text = stringResource(R.string.biometric_disabled),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@Composable
private fun Notice(@StringRes text: Int) {
    Surface(
        color = MaterialTheme.colorScheme.secondaryContainer,
        shape = MaterialTheme.shapes.medium,
        modifier = Modifier
            .fillMaxWidth()
            .semantics { liveRegion = LiveRegionMode.Polite },
    ) {
        Text(
            text = stringResource(text),
            color = MaterialTheme.colorScheme.onSecondaryContainer,
            modifier = Modifier.padding(12.dp),
        )
    }
}

@Composable
private fun Message(@StringRes text: Int) {
    Text(
        text = stringResource(text),
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.padding(vertical = 24.dp),
    )
}

@Composable
private fun Loading() {
    val description = stringResource(R.string.wallet_loading)
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
        CircularProgressIndicator(modifier = Modifier.semantics { contentDescription = description })
    }
}

@Composable
private fun PolicyCardView(card: WalletCard) {
    val policy = card.policy
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .semantics(mergeDescendants = true) {},
        colors = CardDefaults.cardColors(
            containerColor = if (card.expired) {
                MaterialTheme.colorScheme.surfaceVariant
            } else {
                MaterialTheme.colorScheme.primaryContainer
            },
        ),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(
                text = stringResource(R.string.wallet_plan, stringResource(planName(policy.plan))),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Text(stringResource(R.string.wallet_policy_number, policy.policyNumber))
            Text(stringResource(R.string.wallet_holder, policy.holderName))
            Text(stringResource(R.string.wallet_validity, formatDate(policy.validFrom), formatDate(policy.validUntil)))
            if (card.expired) {
                Text(
                    text = stringResource(R.string.wallet_expired),
                    color = MaterialTheme.colorScheme.error,
                    fontWeight = FontWeight.SemiBold,
                )
            }
            policy.coverages.forEach { coverage ->
                Text(
                    text = stringResource(R.string.wallet_coverage, coverage.name, formatMoney(coverage.limit)),
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

@StringRes
private fun planName(plan: String): Int = when (plan) {
    "basic" -> R.string.wallet_plan_basic
    "premium" -> R.string.wallet_plan_premium
    else -> R.string.wallet_plan_standard
}

private fun formatDate(instant: Instant): String = DATE_FORMAT.format(instant.atZone(ZoneId.systemDefault()))

private fun formatMoney(amount: Double): String =
    NumberFormat.getCurrencyInstance(COLOMBIA).apply { maximumFractionDigits = 0 }.format(amount)

@Preview(showBackground = true)
@Composable
private fun WalletScreenPreview() {
    val policy = PolicyCard(
        policyNumber = "POL-2026-00001",
        plan = "premium",
        holderName = "Asegurada de Prueba",
        coverages = listOf(CoverageLimit("Responsabilidad civil", 1e8)),
        validFrom = Instant.parse("2026-01-01T00:00:00Z"),
        validUntil = Instant.parse("2027-01-01T00:00:00Z"),
    )
    SolventaTheme {
        WalletScreen(
            uiState = WalletUiState(loading = false, offline = true, policies = listOf(WalletCard(policy, false))),
            fullName = "Asegurada de Prueba",
            biometricEnabled = true,
            onDisableBiometrics = {},
            onLogout = {},
        )
    }
}

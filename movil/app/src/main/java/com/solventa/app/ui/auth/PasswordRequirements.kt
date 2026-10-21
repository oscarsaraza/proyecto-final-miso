package com.solventa.app.ui.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.solventa.app.R

private const val MIN_LENGTH = 8

fun meetsLength(password: String) = password.length >= MIN_LENGTH

fun mixesLettersAndDigits(password: String) = password.any(Char::isLetter) && password.any(Char::isDigit)

fun passwordRulesMet(password: String, confirmation: String) =
    meetsLength(password) && mixesLettersAndDigits(password) && password == confirmation

// Cada requisito se marca al cumplirse; el lector de pantalla anuncia "cumplido" o "pendiente".
@Composable
fun PasswordRequirements(newPassword: String, confirmation: String, modifier: Modifier = Modifier) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Requirement(stringResource(R.string.recovery_rule_length), meetsLength(newPassword))
        Requirement(stringResource(R.string.recovery_rule_mix), mixesLettersAndDigits(newPassword))
        Requirement(
            stringResource(R.string.recovery_rule_match),
            confirmation.isNotEmpty() && newPassword == confirmation,
        )
    }
}

@Composable
private fun Requirement(text: String, met: Boolean) {
    val state = stringResource(if (met) R.string.recovery_rule_met else R.string.recovery_rule_pending)
    val color = if (met) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier.clearAndSetSemantics { contentDescription = "$text: $state" },
    ) {
        Text(text = if (met) "✓" else "○", color = color, fontWeight = FontWeight.Bold)
        Text(text = text, color = color, style = MaterialTheme.typography.bodySmall)
    }
}

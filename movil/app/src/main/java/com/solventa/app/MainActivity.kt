package com.solventa.app

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import com.solventa.app.data.auth.AndroidBiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.ui.auth.AuthViewModel
import com.solventa.app.ui.auth.BiometricLoginScreen
import com.solventa.app.ui.theme.SolventaTheme

// BiometricPrompt requiere una FragmentActivity para mostrar el diálogo del sistema.
class MainActivity : FragmentActivity() {

    private val authViewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val biometricAuthenticator = AndroidBiometricAuthenticator(this)
        setContent {
            SolventaTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    SolventaMobileRoot(
                        viewModel = authViewModel,
                        biometricAuthenticator = biometricAuthenticator,
                        modifier = Modifier.padding(innerPadding),
                    )
                }
            }
        }
    }
}

@Composable
fun SolventaMobileRoot(
    viewModel: AuthViewModel,
    biometricAuthenticator: BiometricAuthenticator,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsState()

    var biometricPromptLaunched by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        if (!biometricPromptLaunched) {
            biometricPromptLaunched = true
            viewModel.authenticateWithBiometrics(biometricAuthenticator)
        }
    }

    when {
        uiState.isAuthenticated -> HomePlaceholder(modifier)
        uiState.showAlternativeAccess -> AlternativeAccessPlaceholder(
            onBack = viewModel::onBackToBiometrics,
            modifier = modifier,
        )
        else -> BiometricLoginScreen(
            uiState = uiState,
            onAuthenticate = { viewModel.authenticateWithBiometrics(biometricAuthenticator) },
            onUseAlternative = viewModel::onAlternativeAccessSelected,
            modifier = modifier,
        )
    }
}

// Se reemplaza por el formulario de contraseña y código en HU-MOV-02.
@Composable
private fun AlternativeAccessPlaceholder(onBack: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            text = stringResource(R.string.auth_alternative_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )
        Spacer(Modifier.height(8.dp))
        Text(
            text = stringResource(R.string.auth_alternative_pending),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(24.dp))
        OutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth().height(48.dp)) {
            Text(stringResource(R.string.auth_back_to_biometrics))
        }
    }
}

// Se reemplaza por la billetera de pólizas en HU-MOV-04.
@Composable
private fun HomePlaceholder(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            text = stringResource(R.string.home_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = stringResource(R.string.home_subtitle),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

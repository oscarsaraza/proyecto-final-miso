package com.solventa.app

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.fillMaxSize
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
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.solventa.app.data.auth.AndroidBiometricAuthenticator
import com.solventa.app.domain.auth.BiometricAuthenticator
import com.solventa.app.ui.auth.AlternativeLoginScreen
import com.solventa.app.ui.auth.AuthViewModel
import com.solventa.app.ui.auth.BiometricEnrollmentDialog
import com.solventa.app.ui.auth.BiometricLoginScreen
import com.solventa.app.ui.auth.LogoutConfirmationDialog
import com.solventa.app.ui.theme.SolventaTheme

// BiometricPrompt requiere una FragmentActivity para mostrar el diálogo del sistema.
class MainActivity : FragmentActivity() {

    private val authViewModel: AuthViewModel by viewModels {
        viewModelFactory {
            initializer {
                val app = application as SolventaApplication
                AuthViewModel(app.sessionRepository, app.authApi)
            }
        }
    }

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

    if (uiState.offerBiometricEnrollment) {
        BiometricEnrollmentDialog(
            onEnable = { viewModel.enableBiometricUnlock(biometricAuthenticator) },
            onSkip = viewModel::skipBiometricEnrollment,
        )
    }

    if (uiState.showLogoutConfirmation) {
        LogoutConfirmationDialog(onConfirm = viewModel::confirmLogout, onDismiss = viewModel::cancelLogout)
    }

    when {
        uiState.isAuthenticated -> HomePlaceholder(
            fullName = uiState.fullName,
            onLogout = viewModel::requestLogout,
            modifier = modifier,
        )
        uiState.showAlternativeAccess -> AlternativeLoginScreen(
            uiState = uiState,
            onRequestOtp = viewModel::requestOtp,
            onSubmit = { email, password, otpCode ->
                viewModel.authenticateWithPassword(email, password, otpCode, biometricAuthenticator)
            },
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

// Se reemplaza por la billetera de pólizas en HU-MOV-04.
@Composable
private fun HomePlaceholder(fullName: String?, onLogout: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            text = fullName?.let { stringResource(R.string.home_title_named, it) } ?: stringResource(R.string.home_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = stringResource(R.string.home_subtitle),
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(32.dp))
        OutlinedButton(onClick = onLogout) {
            Text(stringResource(R.string.logout_button))
        }
    }
}

package com.solventa.app

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
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
import com.solventa.app.ui.auth.PasswordRecoveryScreen
import com.solventa.app.ui.theme.SolventaTheme
import com.solventa.app.ui.wallet.WalletScreen
import com.solventa.app.ui.wallet.WalletViewModel

// BiometricPrompt requiere una FragmentActivity para mostrar el diálogo del sistema.
class MainActivity : FragmentActivity() {

    private val authViewModel: AuthViewModel by viewModels {
        viewModelFactory {
            initializer {
                val app = application as SolventaApplication
                AuthViewModel(app.sessionRepository, app.authApi, app.policyStore)
            }
        }
    }

    private val walletViewModel: WalletViewModel by viewModels {
        viewModelFactory {
            initializer {
                val app = application as SolventaApplication
                WalletViewModel(app.policiesApi, app.policyStore)
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
                        walletViewModel = walletViewModel,
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
    walletViewModel: WalletViewModel,
    biometricAuthenticator: BiometricAuthenticator,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsState()

    if (uiState.offerBiometricEnrollment) {
        BiometricEnrollmentDialog(
            onEnable = { viewModel.enableBiometricUnlock(biometricAuthenticator) },
            onSkip = viewModel::skipBiometricEnrollment,
        )
    }

    if (uiState.showLogoutConfirmation) {
        LogoutConfirmationDialog(
            biometricEnabled = uiState.biometricEnabled,
            onConfirm = viewModel::confirmLogout,
            onDismiss = viewModel::cancelLogout,
        )
    }

    when {
        uiState.isAuthenticated -> {
            val walletState by walletViewModel.uiState.collectAsState()
            LaunchedEffect(uiState.currentAccountEmail, uiState.offline) {
                uiState.currentAccountEmail?.let {
                    walletViewModel.open(it, if (uiState.offline) null else viewModel.accessToken())
                }
            }
            LaunchedEffect(walletState.sessionExpired) {
                if (walletState.sessionExpired) viewModel.onSessionExpired()
            }
            WalletScreen(
                uiState = walletState,
                fullName = uiState.fullName,
                biometricEnabled = uiState.biometricEnabled,
                onDisableBiometrics = viewModel::disableBiometrics,
                onLogout = viewModel::requestLogout,
                modifier = modifier,
            )
        }
        uiState.showPasswordRecovery -> PasswordRecoveryScreen(
            uiState = uiState,
            onRequestCode = viewModel::requestRecoveryCode,
            onSubmit = viewModel::resetPassword,
            onClose = viewModel::closePasswordRecovery,
            modifier = modifier,
        )
        uiState.showAlternativeAccess -> AlternativeLoginScreen(
            uiState = uiState,
            onRequestOtp = viewModel::requestOtp,
            onSubmit = { email, password, otpCode ->
                viewModel.authenticateWithPassword(email, password, otpCode, biometricAuthenticator)
            },
            onBack = viewModel::onBackToBiometrics,
            onForgotPassword = viewModel::openPasswordRecovery,
            modifier = modifier,
        )
        else -> BiometricLoginScreen(
            uiState = uiState,
            onAuthenticate = { viewModel.authenticateWithBiometrics(biometricAuthenticator) },
            onUseAlternative = viewModel::onAlternativeAccessSelected,
            onSelectAccount = viewModel::selectAccount,
            modifier = modifier,
        )
    }
}

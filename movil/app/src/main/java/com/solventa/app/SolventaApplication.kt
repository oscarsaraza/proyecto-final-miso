package com.solventa.app

import android.app.Application
import com.solventa.app.data.auth.HttpAuthApi
import com.solventa.app.data.policies.EncryptedPolicyStore
import com.solventa.app.data.policies.HttpPoliciesApi
import com.solventa.app.data.policies.KeystoreWalletKeys
import com.solventa.app.data.policies.PassphraseVault
import com.solventa.app.data.session.KeystoreSessionCrypto
import com.solventa.app.data.session.SecureSessionRepository
import com.solventa.app.data.session.SharedPreferencesSessionStore
import com.solventa.app.domain.auth.AuthApi
import com.solventa.app.domain.policies.PoliciesApi
import com.solventa.app.domain.policies.PolicyStore

class SolventaApplication : Application() {

    val sessionRepository: SecureSessionRepository by lazy {
        SecureSessionRepository(KeystoreSessionCrypto(), SharedPreferencesSessionStore(this))
    }

    val authApi: AuthApi by lazy { HttpAuthApi(BuildConfig.API_BASE_URL) }

    val policiesApi: PoliciesApi by lazy { HttpPoliciesApi(BuildConfig.API_BASE_URL) }

    val policyStore: PolicyStore by lazy { EncryptedPolicyStore(this, PassphraseVault(this, KeystoreWalletKeys())) }
}

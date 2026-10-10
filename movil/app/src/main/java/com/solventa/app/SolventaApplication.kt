package com.solventa.app

import android.app.Application
import com.solventa.app.data.auth.HttpAuthApi
import com.solventa.app.data.session.KeystoreSessionCrypto
import com.solventa.app.data.session.SecureSessionRepository
import com.solventa.app.data.session.SharedPreferencesSessionStore
import com.solventa.app.domain.auth.AuthApi

class SolventaApplication : Application() {

    val sessionRepository: SecureSessionRepository by lazy {
        SecureSessionRepository(KeystoreSessionCrypto(), SharedPreferencesSessionStore(this))
    }

    val authApi: AuthApi by lazy { HttpAuthApi(BuildConfig.API_BASE_URL) }
}

package com.solventa.app

import android.app.Application
import com.solventa.app.data.session.KeystoreSessionCrypto
import com.solventa.app.data.session.SecureSessionRepository
import com.solventa.app.data.session.SharedPreferencesSessionStore

class SolventaApplication : Application() {

    val sessionRepository: SecureSessionRepository by lazy {
        SecureSessionRepository(KeystoreSessionCrypto(), SharedPreferencesSessionStore(this))
    }
}

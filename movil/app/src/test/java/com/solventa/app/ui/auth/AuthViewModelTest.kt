package com.solventa.app.ui.auth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class AuthViewModelTest {

    private lateinit var viewModel: AuthViewModel

    @Before
    fun setUp() {
        viewModel = AuthViewModel()
    }

    @Test
    fun `debe inicializar el estado de UI con valores predeterminados`() {
        val state = viewModel.uiState.value
        assertNotNull(state)
        assertFalse(state.isAuthenticated)
        assertEquals(0, state.failedAttempts)
        assertFalse(state.isLocked)
    }

    @Test
    fun `authenticateWithBiometrics debe lanzar NotImplementedError antes de HU-MOV-01`() {
        val exception = assertThrows(NotImplementedError::class.java) {
            viewModel.authenticateWithBiometrics()
        }
        assertTrue(exception.message?.contains("HU-MOV-01") == true)
    }

    @Test
    fun `authenticateWithPin debe lanzar NotImplementedError antes de HU-MOV-02`() {
        val exception = assertThrows(NotImplementedError::class.java) {
            viewModel.authenticateWithPin("1234")
        }
        assertTrue(exception.message?.contains("HU-MOV-02") == true)
    }

    @Test
    fun `logout debe lanzar NotImplementedError antes de HU-MOV-12`() {
        val exception = assertThrows(NotImplementedError::class.java) {
            viewModel.logout()
        }
        assertTrue(exception.message?.contains("HU-MOV-12") == true)
    }
}

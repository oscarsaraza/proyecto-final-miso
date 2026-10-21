package com.solventa.app.ui.auth

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class PasswordFieldTest {

    @get:Rule
    val compose = createComposeRule()

    @Test
    fun `el ojo muestra y oculta la contrasena`() {
        compose.setContent {
            var value by remember { mutableStateOf("") }
            PasswordField(value = value, onValueChange = { value = it }, label = "Contraseña")
        }

        compose.onNodeWithText("Contraseña").performTextInput("Secreta2026")
        compose.onNodeWithText("Secreta2026").assertDoesNotExist()

        compose.onNodeWithContentDescription("Mostrar contraseña").performClick()
        compose.onNodeWithText("Secreta2026").assertIsDisplayed()

        compose.onNodeWithContentDescription("Ocultar contraseña").performClick()
        compose.onNodeWithText("Secreta2026").assertDoesNotExist()
    }
}

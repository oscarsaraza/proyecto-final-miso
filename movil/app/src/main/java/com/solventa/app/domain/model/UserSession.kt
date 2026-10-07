package com.solventa.app.domain.model

data class UserSession(
    val userId: String,
    val documentNumber: String,
    val fullName: String,
    val token: String,
    val isAuthenticated: Boolean = false
)

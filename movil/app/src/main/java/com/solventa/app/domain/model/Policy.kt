package com.solventa.app.domain.model

data class Policy(
    val policyNumber: String,
    val planName: String,
    val insuredAmount: Double,
    val monthlyPremium: Double,
    val status: String,
    val validUntil: String
)

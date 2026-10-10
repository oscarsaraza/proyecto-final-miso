/** Modelos de autenticación y sesión del asesor (HU-WEB-13) */
export interface UserCredentials {
  username: string;
  password: string;
  totpCode: string;
}

export interface UserSession {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  role: string;
  advisorName: string;
  expiresIn?: number;
}

export interface LoginResponseDto {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: string;
  advisor_name: string;
  expires_in: number;
}

export interface RefreshTokenRequestDto {
  refresh_token: string;
}

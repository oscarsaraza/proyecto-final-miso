/** Modelos de autenticación y sesión del asesor */
export interface UserCredentials {
  username: string;
  password: string;
  totpCode: string;
}

export interface UserSession {
  accessToken: string;
  tokenType: string;
  role: string;
  advisorName: string;
}

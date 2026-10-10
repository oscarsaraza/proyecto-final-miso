import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, catchError, map, of, tap, throwError } from 'rxjs';
import {
  LoginResponseDto,
  RefreshTokenRequestDto,
  UserCredentials,
  UserSession,
} from '../models/auth.model';

const SESSION_STORAGE_KEY = 'solventa_advisor_session';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly _currentSession = signal<UserSession | null>(this.loadInitialSession());
  readonly currentSession = this._currentSession.asReadonly();

  private loadInitialSession(): UserSession | null {
    if (typeof window === 'undefined' || !window.sessionStorage) {
      return null;
    }
    try {
      const stored = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored) as UserSession;
      }
    } catch {
      return null;
    }
    return null;
  }

  /**
   * Inicio de sesión del asesor comercial con credenciales corporativas y TOTP (HU-WEB-13)
   */
  login(credentials: UserCredentials): Observable<UserSession> {
    const payload = {
      username: credentials.username,
      password: credentials.password,
      totp_code: credentials.totpCode,
    };

    return this.http
      .post<LoginResponseDto>('/api/v1/experience/auth/login', payload)
      .pipe(
        map((dto) => this.mapDtoToSession(dto)),
        tap((session) => this.persistSession(session)),
      );
  }

  /**
   * Renovación silenciosa de la sesión activa mediante refresh token (HU-WEB-13)
   */
  refreshToken(): Observable<UserSession> {
    const current = this._currentSession();
    if (!current?.refreshToken) {
      this.logout();
      return throwError(() => new Error('No existe refresh token activo para renovar sesión.'));
    }

    const payload: RefreshTokenRequestDto = {
      refresh_token: current.refreshToken,
    };

    return this.http
      .post<LoginResponseDto>('/api/v1/experience/auth/refresh', payload)
      .pipe(
        map((dto) => this.mapDtoToSession(dto)),
        tap((session) => this.persistSession(session)),
        catchError((err) => {
          this.logout();
          return throwError(() => err);
        }),
      );
  }

  /**
   * Cierre de sesión seguro: purga credenciales de sessionStorage y redirige al login
   */
  logout(): void {
    if (typeof window !== 'undefined' && window.sessionStorage) {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
    this._currentSession.set(null);
    this.router.navigate(['/login']);
  }

  /**
   * Determina si existe una sesión válida en memoria
   */
  isAuthenticated(): boolean {
    const session = this._currentSession();
    return session !== null && !!session.accessToken;
  }

  private mapDtoToSession(dto: LoginResponseDto): UserSession {
    return {
      accessToken: dto.access_token,
      refreshToken: dto.refresh_token,
      tokenType: dto.token_type || 'bearer',
      role: dto.role,
      advisorName: dto.advisor_name,
      expiresIn: dto.expires_in,
    };
  }

  private persistSession(session: UserSession): void {
    this._currentSession.set(session);
    if (typeof window !== 'undefined' && window.sessionStorage) {
      try {
        window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
      } catch {
        // En caso de cuota excedida en almacenamiento local
      }
    }
  }
}

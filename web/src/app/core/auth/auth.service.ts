import { Injectable, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { UserCredentials, UserSession } from '../models/auth.model';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly _currentSession = signal<UserSession | null>(null);
  readonly currentSession = this._currentSession.asReadonly();

  /**
   * Inicio de sesión del asesor (Placeholder para HU-WEB-13)
   */
  login(credentials: UserCredentials): Observable<UserSession> {
    throw new Error('HU-WEB-13: Login del asesor comercial pendiente de implementación');
  }

  /**
   * Cierre de sesión (Placeholder)
   */
  logout(): void {
    this._currentSession.set(null);
  }

  /**
   * Verifica si existe una sesión activa
   */
  isAuthenticated(): boolean {
    return this._currentSession() !== null;
  }
}

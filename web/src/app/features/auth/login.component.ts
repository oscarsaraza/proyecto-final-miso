import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-container">
      <div class="login-card">
        <div class="badge">Portal Asesores</div>
        <h2>Iniciar Sesión en Solventa</h2>
        <p class="subtitle">Acceso corporativo seguro con autenticación de dos factores (2FA).</p>

        <div
          *ngIf="errorMessage()"
          class="alert-box"
          [class.alert-danger]="!isLocked()"
          [class.alert-locked]="isLocked()"
          role="alert"
        >
          {{ errorMessage() }}
        </div>

        <form (ngSubmit)="onSubmit()" #loginForm="ngForm">
          <div class="form-group">
            <label for="username">Usuario Corporativo</label>
            <input
              id="username"
              name="username"
              type="email"
              [(ngModel)]="username"
              required
              placeholder="asesor@solventa.com"
              [disabled]="loading()"
            />
          </div>

          <div class="form-group">
            <label for="password">Contraseña</label>
            <input
              id="password"
              name="password"
              type="password"
              [(ngModel)]="password"
              required
              placeholder="••••••••••••"
              [disabled]="loading()"
            />
          </div>

          <div class="form-group">
            <label for="totp">Código 2FA (TOTP)</label>
            <input
              id="totp"
              name="totp"
              type="text"
              maxlength="6"
              [(ngModel)]="totpCode"
              required
              placeholder="123456"
              [disabled]="loading()"
            />
          </div>

          <button type="submit" class="btn-primary" [disabled]="!loginForm.valid || loading()">
            {{ loading() ? 'Iniciando sesión...' : 'Ingresar al Cotizador' }}
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [
    `
      .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: calc(100vh - 120px);
        padding: 24px;
      }
      .login-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 36px;
        width: 100%;
        max-width: 440px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
      }
      .badge {
        display: inline-block;
        background: #e8f3f8;
        color: #0b5474;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 12px;
      }
      h2 {
        margin: 0 0 8px;
        color: #0f172a;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.25;
      }
      .subtitle {
        color: #64748b;
        font-size: 0.875rem;
        line-height: 1.5;
        margin: 0 0 24px;
      }
      .alert-box {
        padding: 12px 14px;
        border-radius: 8px;
        font-size: 0.8125rem;
        font-weight: 500;
        margin-bottom: 20px;
        line-height: 1.45;
      }
      .alert-danger {
        background: #fee2e2;
        border: 1px solid #f87171;
        color: #991b1b;
      }
      .alert-locked {
        background: #fff1f2;
        border: 1px solid #f43f5e;
        color: #881337;
        font-weight: 500;
      }
      .form-group {
        margin-bottom: 16px;
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      label {
        font-size: 0.875rem;
        font-weight: 600;
        color: #1e293b;
        letter-spacing: -0.005em;
      }
      input {
        font-family: inherit;
        font-size: 0.9375rem;
        color: #0f172a;
        padding: 11px 14px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        outline: none;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
      }
      input::placeholder {
        color: #94a1b2;
        font-size: 0.875rem;
      }
      input:focus {
        border-color: #0b5474;
        box-shadow: 0 0 0 3px rgba(11, 84, 116, 0.14);
      }
      input:disabled {
        background: #f1f5f9;
        cursor: not-allowed;
      }
      .btn-primary {
        font-family: inherit;
        width: 100%;
        padding: 13px;
        background: #0b5474;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 0.9375rem;
        font-weight: 600;
        letter-spacing: -0.005em;
        cursor: pointer;
        margin-top: 8px;
        transition: background-color 0.15s ease;
      }
      .btn-primary:hover {
        background: #083f58;
      }
      .btn-primary:disabled {
        background: #94a3b8;
        cursor: not-allowed;
      }
    `,
  ],
})
export class LoginComponent {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  username = '';
  password = '';
  totpCode = '';

  loading = signal<boolean>(false);
  errorMessage = signal<string>('');
  isLocked = signal<boolean>(false);

  onSubmit(): void {
    if (!this.username || !this.password || !this.totpCode) {
      return;
    }

    this.errorMessage.set('');
    this.isLocked.set(false);
    this.loading.set(true);

    this.authService
      .login({
        username: this.username,
        password: this.password,
        totpCode: this.totpCode,
      })
      .subscribe({
        next: () => {
          this.loading.set(false);
          const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/cotizador';
          this.router.navigateByUrl(returnUrl);
        },
        error: (err: HttpErrorResponse) => {
          this.loading.set(false);
          if (err?.status === 423) {
            this.isLocked.set(true);
            this.errorMessage.set(
              err.error?.detail ||
                'Cuenta bloqueada por seguridad tras múltiples intentos fallidos. Intente nuevamente en 15 minutos.',
            );
          } else if (err?.status === 401) {
            this.isLocked.set(false);
            this.errorMessage.set(
              err?.error?.detail ||
                'Credenciales o código de verificación inválidos',
            );
          } else {
            this.isLocked.set(false);
            this.errorMessage.set(
              typeof err?.error?.detail === 'string'
                ? err.error.detail
                : 'Error de comunicación con el servidor. Verifique la conexión.',
            );
          }
        },
      });
  }
}

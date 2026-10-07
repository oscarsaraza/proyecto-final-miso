import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

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
            />
          </div>

          <button type="submit" class="btn-primary" [disabled]="!loginForm.valid">
            Ingresar al Cotizador
          </button>
        </form>

        <div *ngIf="noticeMessage()" class="notice">
          {{ noticeMessage() }}
        </div>
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
        background: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 12px;
      }
      h2 {
        margin: 0 0 8px;
        color: #0f172a;
        font-size: 22px;
      }
      .subtitle {
        color: #64748b;
        font-size: 14px;
        margin: 0 0 24px;
      }
      .form-group {
        margin-bottom: 16px;
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      label {
        font-size: 13px;
        font-weight: 500;
        color: #334155;
      }
      input {
        padding: 10px 14px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        font-size: 14px;
        outline: none;
        transition: border-color 0.2s;
      }
      input:focus {
        border-color: #0284c7;
      }
      .btn-primary {
        width: 100%;
        padding: 12px;
        background: #0284c7;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        margin-top: 8px;
      }
      .btn-primary:hover {
        background: #0369a1;
      }
      .btn-primary:disabled {
        background: #94a3b8;
        cursor: not-allowed;
      }
      .notice {
        margin-top: 16px;
        padding: 12px;
        background: #f8fafc;
        border: 1px dashed #94a3b8;
        border-radius: 8px;
        font-size: 13px;
        color: #475569;
        text-align: center;
      }
    `,
  ],
})
export class LoginComponent {
  username = '';
  password = '';
  totpCode = '';
  noticeMessage = signal<string>('');

  onSubmit(): void {
    // Placeholder para HU-WEB-13
    this.noticeMessage.set(
      'Funcionalidad de autenticación 2FA pendiente de implementación en HU-WEB-13.',
    );
  }
}

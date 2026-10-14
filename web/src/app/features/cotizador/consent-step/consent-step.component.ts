import { Component, inject, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { ConsentRecord, ConsentRequest } from '../../../core/models/consent.model';
import { ConsentService } from '../../../core/consent/consent.service';

interface ConsentResult {
  record?: ConsentRecord;
  error?: string;
}

/** HU-WEB-01 · Registro de consentimiento de tratamiento de datos Open Finance */
@Component({
  selector: 'app-consent-step',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section class="consent-card" aria-labelledby="consent-title">
      <div class="consent-header">
        <h4 id="consent-title">Paso 2: Consentimiento de Tratamiento de Datos</h4>
        <span class="chip" [class.granted]="result().record">
          {{ result().record ? 'Autorizado' : 'Pendiente' }}
        </span>
      </div>

      <p class="description">
        Para perfilar al cliente y tarificar su seguro con datos de Open Finance, se requiere registrar
        la autorización expresa informando finalidad, alcance y vigencia (Ley 1581 de 2012).
      </p>

      <div class="info-grid">
        <div class="info-item">
          <strong>Finalidad:</strong>
          <span>Perfilamiento y cotización de seguro de vida hipotecario con Open Finance.</span>
        </div>
        <div class="info-item">
          <strong>Alcance:</strong>
          <span>Historial crediticio, capacidad de endeudamiento y scoring financiero.</span>
        </div>
        <div class="info-item">
          <strong>Vigencia:</strong>
          <span>30 días calendario a partir del momento de la autorización.</span>
        </div>
      </div>

      <div class="sources-list">
        <strong>Fuentes a consultar bajo autorización:</strong>
        <ul>
          <li><strong>Open Finance:</strong> Agregación financiera y capacidad de pago.</li>
          <li><strong>Burós de Crédito:</strong> Centrales de riesgo e historial crediticio.</li>
          <li><strong>KYC / Identidad:</strong> Verificación de asegurabilidad y listas restrictivas.</li>
        </ul>
      </div>

      @if (result().record; as record) {
        <div class="notice notice-success" role="status">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="9" />
            <path d="M8.5 12.5l2.5 2.5 4.5-5" />
          </svg>
          <div>
            <strong>Consentimiento registrado · {{ record.consent_id }}</strong>
            <p>
              Autorización otorgada para el documento <strong>{{ record.document_number }}</strong>.
              Vigente hasta el {{ record.expires_at | date: 'dd/MM/yyyy' }}.
            </p>
            <div class="hash-box">
              <span class="hash-label">Hash SHA-256 de Auditoría (RC-01 / RC-04):</span>
              <code class="hash-code" data-testid="consent-hash">{{ record.consent_hash }}</code>
            </div>
          </div>
        </div>
      } @else {
        @if (result().error; as error) {
          <div class="notice notice-error" role="alert">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M15 9l-6 6M9 9l6 6" />
            </svg>
            <div>
              <strong>No se pudo registrar el consentimiento</strong>
              <p>{{ error }}</p>
            </div>
          </div>
        }

        <form class="consent-form" (ngSubmit)="submitConsent()">
          <div class="form-row">
            <label for="docNumber">Documento del cliente</label>
            <input
              id="docNumber"
              name="docNumber"
              type="text"
              [ngModel]="docNumber()"
              (ngModelChange)="docNumber.set($event)"
              [disabled]="registering()"
              required
            />
          </div>

          <div class="form-row">
            <label for="otpCode">
              Código OTP de verificación (SMS cliente)
              <span class="hint">(Simulado: use 839201 o cualquier código de 6 dígitos)</span>
            </label>
            <input
              id="otpCode"
              name="otpCode"
              type="text"
              maxlength="6"
              [ngModel]="otpCode()"
              (ngModelChange)="otpCode.set($event)"
              [disabled]="registering()"
              required
            />
          </div>

          <div class="form-checkbox">
            <input
              id="termsAccepted"
              name="termsAccepted"
              type="checkbox"
              [ngModel]="termsAccepted()"
              (ngModelChange)="termsAccepted.set($event)"
              [disabled]="registering()"
            />
            <label for="termsAccepted">
              El cliente autoriza de manera previa, expresa e informada el tratamiento de sus datos
              financieros y de scoring para la finalidad descrita.
            </label>
          </div>

          <button
            type="submit"
            class="submit-button"
            [disabled]="registering() || !termsAccepted() || !otpCode() || otpCode().length !== 6"
          >
            {{ registering() ? 'Registrando autorización...' : 'Registrar consentimiento' }}
          </button>
        </form>
      }
    </section>
  `,
  styles: [`
    .consent-card {
      margin-top: 24px;
      padding: 24px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .consent-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .consent-header h4 {
      margin: 0;
      color: #0f172a;
      font-size: 1.125rem;
      font-weight: 700;
    }
    .chip {
      padding: 4px 10px;
      background: #fef3c7;
      color: #92400e;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .chip.granted {
      background: #dcfce7;
      color: #166534;
    }
    .description {
      margin: 0 0 16px;
      color: #64748b;
      font-size: 0.875rem;
      line-height: 1.5;
    }
    .info-grid {
      display: grid;
      gap: 10px;
      padding: 12px 16px;
      background: #f8fafc;
      border-radius: 8px;
      margin-bottom: 16px;
      border: 1px solid #f1f5f9;
    }
    .info-item {
      font-size: 0.8125rem;
      color: #334155;
    }
    .info-item strong {
      color: #0f172a;
      margin-right: 6px;
    }
    .sources-list {
      font-size: 0.8125rem;
      color: #475569;
      margin-bottom: 16px;
    }
    .sources-list ul {
      margin: 6px 0 0;
      padding-left: 20px;
    }
    .sources-list li {
      margin-bottom: 4px;
    }
    .consent-form {
      display: grid;
      gap: 16px;
      margin-top: 16px;
    }
    .form-row {
      display: grid;
      gap: 6px;
    }
    .form-row label {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #334155;
    }
    .hint {
      font-weight: 400;
      color: #64748b;
      font-size: 0.75rem;
      margin-left: 6px;
    }
    .form-row input {
      padding: 10px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 0.875rem;
      color: #0f172a;
    }
    .form-row input:focus {
      outline: none;
      border-color: #0b5474;
      box-shadow: 0 0 0 2px rgba(11, 84, 116, 0.2);
    }
    .form-checkbox {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      font-size: 0.8125rem;
      color: #334155;
      line-height: 1.4;
    }
    .form-checkbox input {
      margin-top: 3px;
      accent-color: #0b5474;
      width: 16px;
      height: 16px;
    }
    .submit-button {
      padding: 12px 16px;
      background: #0b5474;
      color: #ffffff;
      border: 0;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease;
    }
    .submit-button:hover:not(:disabled) {
      background: #083f58;
    }
    .submit-button:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }
    .hash-box {
      margin-top: 10px;
      padding: 8px 10px;
      background: #f1f5f9;
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .hash-label {
      font-size: 0.6875rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: #64748b;
      font-weight: 700;
    }
    .hash-code {
      font-family: monospace;
      font-size: 0.75rem;
      word-break: break-all;
      color: #0b5474;
      font-weight: 600;
    }
  `],
})
export class ConsentStepComponent {
  readonly documentNumber = input<string>('1020304050');
  readonly consentGranted = output<ConsentRecord>();

  readonly docNumber = signal<string>('1020304050');
  readonly otpCode = signal<string>('839201');
  readonly termsAccepted = signal<boolean>(false);
  readonly registering = signal<boolean>(false);
  readonly result = signal<ConsentResult>({});

  private readonly consentService = inject(ConsentService);

  submitConsent(): void {
    if (!this.termsAccepted() || !this.otpCode() || this.otpCode().length !== 6) {
      return;
    }

    this.registering.set(true);
    this.result.set({});

    const request: ConsentRequest = {
      document_number: this.docNumber(),
      channel: 'web',
      otp_code: this.otpCode(),
      terms_accepted: this.termsAccepted(),
      purpose: 'Perfilamiento y cotización de seguro de vida hipotecario con Open Finance',
      scope: 'Historial crediticio, capacidad de endeudamiento y scoring financiero',
      validity_days: 30,
    };

    this.consentService
      .registerConsent(request)
      .pipe(finalize(() => this.registering.set(false)))
      .subscribe({
        next: (record) => {
          this.result.set({ record });
          this.consentGranted.emit(record);
        },
        error: (error: HttpErrorResponse) => {
          const detail = error.error?.detail || 'Error al registrar el consentimiento.';
          this.result.set({ error: detail });
        },
      });
  }
}

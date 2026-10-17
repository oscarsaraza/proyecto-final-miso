import { Component, computed, inject, input, linkedSignal, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { ConsentRecord, ConsentRequest } from '../../../core/models/consent.model';
import { ConsentService } from '../../../core/consent/consent.service';
import { ClientIdentification, RiskData } from '../../../core/models/client.model';
import { COP } from '../../../core/money';

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
          Estado del consentimiento: {{ result().record ? 'Autorizado' : 'Pendiente' }}
        </span>
      </div>

      <p class="description">
        Para perfilar al cliente y cotizar su seguro con datos de Open Finance, se requiere
        registrar la autorización expresa informando finalidad, alcance y vigencia (Ley 1581 de
        2012).
      </p>

      @if (clientData(); as client) {
        <div class="client-summary-card">
          <div class="summary-col">
            <span class="summary-label">Titular Solicitante:</span>
            <strong class="summary-val">{{ client.first_name }} {{ client.last_name }}</strong>
            <span class="summary-sub"
              >{{ client.document_type }} {{ client.document_number }} · {{ client.phone }}</span
            >
          </div>
          @if (riskData(); as risk) {
            <div class="summary-col">
              <span class="summary-label">Monto Solicitado:</span>
              <strong class="summary-amount">{{ formatMoney(risk.insured_amount) }}</strong>
              <span class="summary-sub"
                >{{ risk.term_months }} meses · {{ risk.financial_entity }}</span
              >
            </div>
          }
        </div>
      }

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
              Autorización otorgada para el documento <strong>{{ record.document_number }}</strong
              >. Vigente hasta el {{ record.expires_at | date: 'dd/MM/yyyy' }}.
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
          <div class="form-row-group">
            <div class="form-row">
              <label for="validityDays">Vigencia del consentimiento</label>
              <select
                id="validityDays"
                name="validityDays"
                [ngModel]="validityDays()"
                (ngModelChange)="validityDays.set(+$event)"
                [disabled]="registering()"
              >
                <option [value]="15">15 días calendario</option>
                <option [value]="30">30 días calendario (estándar)</option>
                <option [value]="60">60 días calendario</option>
                <option [value]="90">90 días calendario</option>
                <option [value]="365">365 días (1 año)</option>
              </select>
            </div>

            <div class="form-row">
              <label for="otpCode">Código OTP de verificación (SMS cliente)</label>
              <input
                id="otpCode"
                name="otpCode"
                type="text"
                inputmode="numeric"
                pattern="[0-9]{6}"
                maxlength="6"
                autocomplete="one-time-code"
                [ngModel]="otpCode()"
                (ngModelChange)="otpCode.set($event)"
                [disabled]="registering()"
                required
              />
            </div>
          </div>

          <div class="form-row-group">
            <div class="form-row">
              <label for="purpose">Finalidad de la autorización</label>
              <textarea
                id="purpose"
                name="purpose"
                rows="3"
                [ngModel]="purpose()"
                (ngModelChange)="purpose.set($event)"
                [disabled]="registering()"
                required
              ></textarea>
            </div>

            <div class="form-row">
              <label for="scope">Alcance de los datos a consultar</label>
              <textarea
                id="scope"
                name="scope"
                rows="3"
                [ngModel]="scope()"
                (ngModelChange)="scope.set($event)"
                [disabled]="registering()"
                required
              ></textarea>
            </div>
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

          <div class="actions-group">
            @if (clientData()) {
              <button type="button" class="back-button" (click)="requestBack.emit()">
                &larr; Modificar datos del cliente
              </button>
            }
            <button
              type="submit"
              class="submit-button"
              [disabled]="
                registering() ||
                !termsAccepted() ||
                !isOtpValid() ||
                !docNumber() ||
                !purpose() ||
                !scope()
              "
            >
              {{ registering() ? 'Registrando autorización...' : 'Registrar consentimiento' }}
            </button>
          </div>
        </form>

        <div class="sources-list">
          <strong>Fuentes a consultar bajo autorización:</strong>
          <ul>
            <li><strong>Open Finance:</strong> Agregación financiera y capacidad de pago.</li>
            <li><strong>Burós de Crédito:</strong> Centrales de riesgo e historial crediticio.</li>
            <li>
              <strong>KYC / Identidad:</strong> Verificación de asegurabilidad y listas
              restrictivas.
            </li>
          </ul>
        </div>

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
      }
    </section>
  `,
  styles: [
    `
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
      .form-row-group {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      .form-row-group.align-center {
        align-items: center;
      }
      @media (max-width: 560px) {
        .form-row-group {
          grid-template-columns: 1fr;
        }
      }
      .form-row {
        display: grid;
        flex-direction: column;
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
      .form-row input,
      .form-row select,
      .form-row textarea {
        padding: 10px 12px;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        font-size: 0.875rem;
        color: #0f172a;
        background: #ffffff;
        font-family: inherit;
        resize: vertical;
        box-sizing: border-box;
      }
      .form-row input:focus,
      .form-row select:focus,
      .form-row textarea:focus {
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
        cursor: pointer;
      }
      .form-checkbox label {
        cursor: pointer;
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
      .client-summary-card {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        padding: 16px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 20px;
      }
      .summary-col {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .summary-label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }
      .summary-val {
        font-size: 0.9375rem;
        color: #0f172a;
      }
      .summary-sub {
        font-size: 0.8125rem;
        color: #64748b;
      }
      .summary-amount {
        font-size: 1.0625rem;
        color: #0b5474;
      }
      .actions-group {
        display: flex;
        gap: 12px;
        justify-content: flex-end;
        align-items: center;
        flex-wrap: wrap;
        margin-top: 12px;
      }
      .back-button {
        padding: 10px 14px;
        background: transparent;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        color: #475569;
        font-size: 0.875rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .back-button:hover {
        background: #f1f5f9;
        border-color: #94a3b8;
      }
    `,
  ],
})
export class ConsentStepComponent {
  readonly clientData = input<ClientIdentification | null>(null);
  readonly riskData = input<RiskData | null>(null);
  readonly documentNumber = input<string>('1020304050');
  readonly consentGranted = output<ConsentRecord>();
  readonly requestBack = output<void>();

  formatMoney(amount: number): string {
    return COP.format(amount);
  }

  readonly docNumber = linkedSignal(() => this.documentNumber());
  readonly otpCode = signal<string>('839201');
  readonly termsAccepted = signal<boolean>(false);
  readonly registering = signal<boolean>(false);
  readonly result = signal<ConsentResult>({});

  readonly purpose = signal<string>(
    'Perfilamiento y cotización de seguro de vida hipotecario con Open Finance',
  );
  readonly scope = signal<string>(
    'Historial crediticio, capacidad de endeudamiento y scoring financiero',
  );
  readonly validityDays = signal<number>(30);

  readonly isOtpValid = computed(() => /^\d{6}$/.test(this.otpCode()));

  private readonly consentService = inject(ConsentService);

  submitConsent(): void {
    if (
      !this.termsAccepted() ||
      !this.isOtpValid() ||
      !this.docNumber() ||
      !this.purpose() ||
      !this.scope()
    ) {
      return;
    }

    this.registering.set(true);
    this.result.set({});

    const request: ConsentRequest = {
      document_number: this.docNumber(),
      channel: 'web',
      otp_code: this.otpCode(),
      terms_accepted: this.termsAccepted(),
      purpose: this.purpose(),
      scope: this.scope(),
      validity_days: this.validityDays(),
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

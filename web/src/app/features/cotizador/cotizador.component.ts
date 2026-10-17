import { Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { ClientIdentification, ClientQuoteSubmission, RiskData } from '../../core/models/client.model';
import { ConsentRecord } from '../../core/models/consent.model';
import { PolicyRecord } from '../../core/models/policy.model';
import { PlanTier, QuoteRequest, QuoteResponse } from '../../core/models/quote.model';
import { PolicyService } from '../../core/policies/policy.service';
import { QuoteService } from '../../core/quotes/quote.service';
import { ClientDataStepComponent } from './client-data-step/client-data-step.component';
import { ConsentStepComponent } from './consent-step/consent-step.component';
import { PaymentStepComponent } from './payment-step/payment-step.component';
import { PremiumBreakdownComponent } from './premium-breakdown/premium-breakdown.component';

interface Emission {
  policy?: PolicyRecord;
  error?: 'expired' | 'failed';
}

@Component({
  selector: 'app-cotizador',
  standalone: true,
  imports: [
    CommonModule,
    ClientDataStepComponent,
    ConsentStepComponent,
    PaymentStepComponent,
    PremiumBreakdownComponent,
  ],
  template: `
    <div class="cotizador-container">
      <div class="cotizador-header">
        <h1>Cotizador de Seguros de Vida</h1>
        <p>Proceso comercial guiado: Identificación, Consentimiento, Cotización, Coberturas y Recaudo.</p>
      </div>

      <div class="steps-progress">
        <div class="step" [class.active]="currentStep() === 1" [class.completed]="currentStep() > 1">1. Identificación</div>
        <div class="step" [class.active]="currentStep() === 2" [class.completed]="currentStep() > 2 || !!consent()">2. Consentimiento</div>
        <div class="step" [class.active]="currentStep() === 3 && !quote()" [class.completed]="!!quote()">3. Cotización</div>
        <div class="step" [class.active]="!!quote() && !emission().policy" [class.completed]="!!emission().policy">4. Coberturas</div>
        <div class="step" [class.active]="!!emission().policy">5. Emisión y Pago</div>
      </div>

      <!-- Paso 1: Captura de Datos del Cliente y Riesgo (HU-WEB-02) -->
      @if (currentStep() === 1) {
        <app-client-data-step
          [initialClient]="client()"
          [initialRisk]="risk()"
          (clientDataSubmitted)="onClientDataSubmitted($event)"
        />
      }

      <!-- Paso 2: Consentimiento de Tratamiento de Datos (HU-WEB-01) -->
      @if (currentStep() >= 2) {
        <app-consent-step
          [clientData]="client()"
          [riskData]="risk()"
          [documentNumber]="client()?.document_number || '1020304050'"
          (consentGranted)="onConsentGranted($event)"
          (requestBack)="currentStep.set(1)"
        />
      }

      @if (quoting()) {
        <div class="notice notice-info" role="status" style="margin-top: 24px;">
          <div class="spinner-blue" aria-hidden="true"></div>
          <div>
            <strong>Calculando cotización personalizada...</strong>
            <p>Consultando reglas actuariales y scoring de Open Finance para generar los planes.</p>
          </div>
        </div>
      }

      @if (quoteError(); as err) {
        <div class="notice notice-error" role="alert" style="margin-top: 24px;">
          <div>
            <strong>Error al calcular la cotización:</strong>
            <p>{{ err }}</p>
          </div>
          <button type="button" class="btn-retry" (click)="requestQuote()">Reintentar</button>
        </div>
      }

      @if (selectedTierDetail(); as tier) {
        <div class="quote-result">
          @if (quote()!.status === 'degraded') {
            <div class="notice notice-warning" role="alert">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
                stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M10.3 4.3L2.6 17.5A2 2 0 004.3 20.5h15.4a2 2 0 001.7-3L13.7 4.3a2 2 0 00-3.4 0z" />
                <path d="M12 9v4M12 16.5h.01" />
              </svg>
              <div>
                <strong>Cotización calculada con perfil parcial por latencia en proveedores de scoring</strong>
                <p>La tarifa aplica la tabla base conservadora y podrá reajustarse o ratificarse en la suscripción definitiva.</p>
              </div>
            </div>
          }
          <div class="tier-tabs" role="tablist" aria-label="Planes cotizados">
            @for (option of quote()!.tiers; track option.tier) {
              <button
                type="button"
                role="tab"
                class="tier-tab"
                [class.active]="option.tier === selectedTier()"
                [attr.aria-selected]="option.tier === selectedTier()"
                (click)="selectedTier.set(option.tier)"
              >
                {{ tierLabels[option.tier] }}
              </button>
            }
          </div>
          <app-premium-breakdown [tier]="tier" />
          @if (emission().policy; as policy) {
            <div class="notice notice-success" role="status">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
                stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="M8.5 12.5l2.5 2.5 4.5-5" />
              </svg>
              <div>
                <strong>Póliza emitida {{ policy.policy_number }}</strong>
                <p>
                  Plan {{ tierLabels[policy.conditions.tier] }} · vigente del
                  {{ policy.issued_at | date: 'dd/MM/yyyy' }} al {{ policy.valid_until | date: 'dd/MM/yyyy' }}
                </p>
              </div>
            </div>
            <app-payment-step [policy]="policy" />
          } @else if (emission().error === 'expired') {
            <div class="notice notice-error" role="alert">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
                stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="M15 9l-6 6M9 9l6 6" />
              </svg>
              <div>
                <strong>La cotización venció</strong>
                <p>Las tarifas deben recalcularse antes de emitir la póliza.</p>
                <!-- HU-WEB-02 vuelve a solicitar la cotización con los datos capturados. -->
                <button type="button" (click)="requestQuote()">Recotizar con datos actuales</button>
              </div>
            </div>
          } @else {
            @if (emission().error === 'failed') {
              <p class="issue-error" role="alert">No se pudo emitir la póliza. Intente de nuevo.</p>
            }
            <button type="button" class="issue-button" [disabled]="issuing()" (click)="issuePolicy()">
              Emitir póliza
            </button>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .cotizador-container {
      max-width: 900px;
      margin: 32px auto;
      padding: 0 20px;
    }
    .cotizador-header h1 {
      margin: 0 0 6px;
      color: #0f172a;
      font-size: 1.625rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .cotizador-header p {
      margin: 0 0 24px;
      color: #64748b;
      font-size: 0.875rem;
      line-height: 1.55;
    }
    .steps-progress {
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }
    .step {
      padding: 8px 16px;
      background: #f1f5f9;
      border-radius: 20px;
      font-size: 0.8125rem;
      color: #64748b;
      font-weight: 600;
      letter-spacing: -0.005em;
    }
    .step.active {
      background: #0b5474;
      color: #ffffff;
    }
    .step.completed {
      background: #059669;
      color: #ffffff;
    }
    .content-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .content-card h3 {
      margin-top: 0;
      color: #1e293b;
      font-size: 1.125rem;
      font-weight: 600;
      letter-spacing: -0.01em;
    }
    .content-card p {
      font-size: 0.875rem;
      color: #64748b;
      margin-bottom: 12px;
    }
    .quote-result {
      margin-top: 24px;
      display: grid;
      gap: 12px;
    }
    .issue-button {
      padding: 12px 16px;
      border: 0;
      border-radius: 8px;
      background: #0b5474;
      color: #fff;
      font-weight: 600;
      cursor: pointer;
    }
    .issue-button:disabled {
      opacity: 0.6;
      cursor: progress;
    }
    .issue-error {
      margin: 0;
      color: #b91c1c;
      font-size: 0.8125rem;
    }
    .tier-tabs {
      display: flex;
      gap: 8px;
    }
    .tier-tab {
      padding: 8px 16px;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      background: #fff;
      color: #475569;
      cursor: pointer;
    }
    .tier-tab.active {
      background: #0b5474;
      border-color: #0b5474;
      color: #fff;
    }
    .content-card ul {
      padding-left: 20px;
      color: #475569;
      font-size: 0.875rem;
      line-height: 1.75;
    }
    .notice.notice-info {
      background: #f0f9ff;
      border: 1px solid #bae6fd;
      color: #0369a1;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      border-radius: 8px;
    }
    .spinner-blue {
      width: 20px;
      height: 20px;
      border: 2px solid rgba(11, 84, 116, 0.2);
      border-top-color: #0b5474;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      flex-shrink: 0;
    }
    .btn-retry {
      margin-left: auto;
      padding: 6px 12px;
      background: #b91c1c;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 0.8125rem;
      font-weight: 600;
      cursor: pointer;
    }
  `]
})
export class CotizadorComponent {
  // HU-WEB-02 datos del solicitante y condiciones del riesgo asegurado.
  readonly client = signal<ClientIdentification | null>(null);
  readonly risk = signal<RiskData | null>(null);
  readonly currentStep = signal<number>(1);
  readonly quoting = signal<boolean>(false);
  readonly quoteError = signal<string | null>(null);

  // HU-WEB-01 registro y estado del consentimiento informado.
  readonly consent = signal<ConsentRecord | null>(null);
  // HU-WEB-02 asigna la cotización devuelta por QuoteService.
  readonly quote = signal<QuoteResponse | null>(null);

  private readonly quotes = inject(QuoteService);
  private readonly policies = inject(PolicyService);

  onClientDataSubmitted(submission: ClientQuoteSubmission): void {
    this.client.set(submission.client);
    this.risk.set(submission.risk);
    this.currentStep.set(2);
  }

  onConsentGranted(record: ConsentRecord): void {
    this.consent.set(record);
    this.currentStep.set(3);
    this.requestQuote();
  }

  requestQuote(): void {
    this.quote.set(null);
    const doc = this.consent()?.document_number || this.client()?.document_number || '1020304050';
    const req: QuoteRequest = {
      document_type: this.client()?.document_type ?? 'CC',
      document_number: doc,
      birth_date: this.client()?.birth_date ?? '1990-05-15',
      insured_amount: this.risk()?.insured_amount ?? 150_000_000,
      city: this.risk()?.city ?? 'Bogotá',
      occupation_risk: this.risk()?.occupation_risk ?? 1,
    };

    this.quoting.set(true);
    this.quoteError.set(null);
    this.quotes
      .createQuote(req)
      .pipe(finalize(() => this.quoting.set(false)))
      .subscribe({
        next: (res) => this.quote.set(res),
        error: (error: HttpErrorResponse) => {
          this.quoteError.set(error.error?.detail || 'Error al conectar con el motor de cotización.');
        },
      });
  }

  readonly selectedTier = signal<PlanTier>('standard');
  readonly selectedTierDetail = computed(
    () => this.quote()?.tiers.find((tier) => tier.tier === this.selectedTier()) ?? null,
  );
  readonly tierLabels: Record<PlanTier, string> = {
    basic: 'Básico',
    standard: 'Estándar',
    premium: 'Premium',
  };

  // Una cotización nueva descarta la emisión de la anterior.
  readonly emission = linkedSignal<QuoteResponse | null, Emission>({
    source: this.quote,
    computation: () => ({}),
  });
  readonly issuing = signal(false);

  issuePolicy(): void {
    this.issuing.set(true);
    this.policies
      .issuePolicy({ quote_id: this.quote()!.quote_id, tier: this.selectedTier() })
      .pipe(finalize(() => this.issuing.set(false)))
      .subscribe({
        next: (policy) => this.emission.set({ policy }),
        error: (error: HttpErrorResponse) => this.emission.set({ error: error.status === 409 ? 'expired' : 'failed' }),
      });
  }
}

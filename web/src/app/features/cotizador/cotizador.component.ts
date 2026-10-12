import { Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { PolicyRecord } from '../../core/models/policy.model';
import { PlanTier, QuoteResponse } from '../../core/models/quote.model';
import { PolicyService } from '../../core/policies/policy.service';
import { PremiumBreakdownComponent } from './premium-breakdown/premium-breakdown.component';

interface Emission {
  policy?: PolicyRecord;
  error?: 'expired' | 'failed';
}

@Component({
  selector: 'app-cotizador',
  standalone: true,
  imports: [CommonModule, PremiumBreakdownComponent],
  template: `
    <div class="cotizador-container">
      <div class="cotizador-header">
        <h1>Cotizador de Seguros de Vida</h1>
        <p>Proceso comercial guiado: Identificación, Consentimiento, Cotización, Coberturas y Recaudo.</p>
      </div>

      <div class="steps-progress">
        <div class="step active">1. Identificación</div>
        <div class="step">2. Consentimiento</div>
        <div class="step">3. Tarificación</div>
        <div class="step">4. Coberturas</div>
        <div class="step">5. Emisión y Pago</div>
      </div>

      <div class="content-card">
        <h3>Estructura base del flujo comercial lista para desarrollo</h3>
        <p>Las siguientes historias de usuario implementarán cada paso de este componente:</p>
        <ul>
          <li><strong>HU-WEB-02:</strong> Captura de datos del cliente e identificación inicial.</li>
          <li><strong>HU-WEB-01:</strong> Captura y auditoría del consentimiento Open Finance.</li>
          <li><strong>HU-WEB-03 & 04:</strong> Cálculo de prima en memoria con degradación ante caída de burós.</li>
          <li><strong>HU-WEB-05:</strong> Configuración de coberturas y emisión contractual.</li>
          <li><strong>HU-WEB-06:</strong> Pago con garantía de idempotencia.</li>
        </ul>
      </div>

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
                <!-- HU-WEB-02 volverá a pedir la cotización con los datos del formulario. -->
                <button type="button" (click)="quote.set(null)">Recotizar con datos actuales</button>
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
    .notice {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 16px;
      border: 1px solid;
      border-radius: 8px;
      font-size: 0.8125rem;
    }
    .notice svg {
      flex: none;
    }
    .notice p {
      margin: 4px 0 0;
    }
    .notice button {
      margin-top: 8px;
      padding: 6px 12px;
      border: 1px solid currentColor;
      border-radius: 6px;
      background: #fff;
      color: inherit;
      cursor: pointer;
    }
    .notice-warning {
      border-color: rgba(180, 83, 9, 0.25);
      background: #fdf4e7;
      color: #b45309;
    }
    .notice-success {
      border-color: rgba(21, 128, 61, 0.25);
      background: #e9f7ee;
      color: #15803d;
    }
    .notice-error {
      border-color: rgba(185, 28, 28, 0.25);
      background: #fdeeee;
      color: #b91c1c;
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
  `]
})
export class CotizadorComponent {
  // HU-WEB-02 asigna la cotización devuelta por QuoteService.
  readonly quote = signal<QuoteResponse | null>(null);
  readonly selectedTier = signal<PlanTier>('standard');
  readonly selectedTierDetail = computed(
    () => this.quote()?.tiers.find((tier) => tier.tier === this.selectedTier()) ?? null,
  );
  readonly tierLabels: Record<PlanTier, string> = {
    basic: 'Básico',
    standard: 'Estándar',
    premium: 'Premium',
  };

  private readonly policies = inject(PolicyService);
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

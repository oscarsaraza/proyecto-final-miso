import { Component, computed, inject, input, linkedSignal, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { COP } from '../../../core/money';
import { PaymentMethod, PaymentReceipt } from '../../../core/models/payment.model';
import { PolicyRecord } from '../../../core/models/policy.model';
import { PaymentService } from '../../../core/payments/payment.service';

interface PaymentOption {
  label: string;
  method: PaymentMethod;
  token: string;
}

interface PaymentResult {
  receipt?: PaymentReceipt;
  declined?: string;
  failed?: boolean;
}

// Sin pasarela real, cada opción es el token que devolvería su formulario; nunca datos de tarjeta (HA-15).
export const PAYMENT_OPTIONS: PaymentOption[] = [
  { label: 'PSE · Bancolombia', method: 'PSE', token: 'tok_pse_bancolombia' },
  { label: 'Tarjeta terminada en 4417', method: 'CARD', token: 'tok_card_4417' },
  { label: 'PSE · cuenta sin fondos (prueba)', method: 'PSE', token: 'tok_insufficient_funds' },
];

/** HU-WEB-06 · Cobro de la primera prima sin duplicar el cargo */
@Component({
  selector: 'app-payment-step',
  standalone: true,
  template: `
    @if (result().receipt; as receipt) {
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
          <strong>Pago aprobado · recibo {{ receipt.receipt_number }}</strong>
          <p>Se cobraron {{ total() }} y la póliza {{ receipt.policy_number }} quedó activa.</p>
        </div>
      </div>
    } @else {
      <section class="payment" aria-labelledby="payment-title">
        <h4 id="payment-title">Pago de la primera prima</h4>
        <fieldset [disabled]="paying()">
          <legend>Medio de pago</legend>
          @for (candidate of options; track candidate.token) {
            <label>
              <input
                type="radio"
                name="payment-option"
                [checked]="candidate === option()"
                (change)="option.set(candidate)"
              />
              {{ candidate.label }}
            </label>
          }
        </fieldset>
        <p class="idempotency">
          Clave de idempotencia <code>{{ idempotencyKey() }}</code
          >. Si reintenta el pago, esta clave impide un segundo cobro.
        </p>
        @if (result().declined; as detail) {
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
            <strong>{{ detail }}</strong>
          </div>
        }
        @if (result().failed) {
          <p class="pay-error" role="alert">
            No se pudo confirmar el pago. Reintente: con la misma clave no se cobrará dos veces.
          </p>
        }
        <button type="button" class="pay-button" [disabled]="paying()" (click)="pay()">
          Pagar {{ total() }}
        </button>
      </section>
    }
  `,
  styles: [
    `
      .payment {
        display: grid;
        gap: 12px;
        padding: 16px;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        background: #fff;
      }
      h4 {
        font-size: 1rem;
      }
      fieldset {
        display: grid;
        gap: 8px;
        margin: 0;
        padding: 0;
        border: 0;
        font-size: 0.875rem;
      }
      legend {
        margin-bottom: 8px;
        color: #475569;
        font-weight: 600;
      }
      .idempotency {
        color: #64748b;
        font-size: 0.75rem;
      }
      .pay-button {
        padding: 12px 16px;
        border: 0;
        border-radius: 8px;
        background: #0b5474;
        color: #fff;
        font-weight: 600;
        cursor: pointer;
      }
      .pay-button:disabled {
        opacity: 0.6;
        cursor: progress;
      }
      .pay-error {
        color: #b91c1c;
        font-size: 0.8125rem;
      }
    `,
  ],
})
export class PaymentStepComponent {
  readonly policy = input.required<PolicyRecord>();
  readonly options = PAYMENT_OPTIONS;
  readonly option = signal(PAYMENT_OPTIONS[0]);
  // Una clave por intento: se conserva en los reintentos y cambia con el medio de pago.
  readonly idempotencyKey = linkedSignal({
    source: this.option,
    computation: () => crypto.randomUUID(),
  });
  readonly result = linkedSignal<string, PaymentResult>({
    source: this.idempotencyKey,
    computation: () => ({}),
  });
  readonly paying = signal(false);
  readonly total = computed(() => COP.format(this.policy().conditions.monthly_premium));

  private readonly payments = inject(PaymentService);

  pay(): void {
    const { method, token } = this.option();
    const request = {
      policy_number: this.policy().policy_number,
      amount: this.policy().conditions.monthly_premium,
      payment_method: method,
      token_or_account: token,
    };
    this.paying.set(true);
    this.payments
      .charge(request, this.idempotencyKey())
      .pipe(finalize(() => this.paying.set(false)))
      .subscribe({
        next: (receipt) => this.result.set({ receipt }),
        error: (error: HttpErrorResponse) =>
          this.result.set(
            error.status === 402 ? { declined: error.error.detail } : { failed: true },
          ),
      });
  }
}

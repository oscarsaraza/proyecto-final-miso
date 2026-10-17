import { Component, computed, inject, input, linkedSignal, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import {
  ClientIdentification,
  ClientQuoteSubmission,
  RiskData,
} from '../../../core/models/client.model';
import { ClientService } from '../../../core/client/client.service';
import { COP } from '../../../core/money';

/** HU-WEB-02 · Captura de datos del cliente y del riesgo para cotización */
@Component({
  selector: 'app-client-data-step',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section class="step-card" aria-labelledby="step1-title">
      <div class="step-header">
        <div>
          <h4 id="step1-title">Paso 1: Identificación y Datos del Riesgo</h4>
          <p class="subtitle">
            Capture los datos sociodemográficos del cliente y del crédito hipotecario para evaluar
            su asegurabilidad y calcular la prima personalizada.
          </p>
        </div>
        <span
          class="chip"
          [class.ok]="isAgeValid()"
          [class.error]="calculatedAge() !== null && !isAgeValid()"
        >
          {{ isAgeValid() ? 'Elegible' : calculatedAge() !== null ? 'No asegurable' : 'Pendiente' }}
        </span>
      </div>

      <form (ngSubmit)="onSubmit()" novalidate>
        <!-- Panel 1: Datos del Titular -->
        <fieldset class="panel-section">
          <legend class="section-legend">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            Datos del Titular Solicitante
          </legend>

          <div class="fields-grid">
            <div class="form-group">
              <label for="docType">Tipo de Documento</label>
              <select
                id="docType"
                [ngModel]="documentType()"
                (ngModelChange)="documentType.set($event)"
                name="docType"
                required
              >
                <option value="CC">Cédula de ciudadanía (CC)</option>
                <option value="CE">Cédula de extranjería (CE)</option>
                <option value="PAS">Pasaporte (PAS)</option>
              </select>
            </div>

            <div class="form-group">
              <label for="docNumber">Número de documento</label>
              <input
                id="docNumber"
                type="text"
                inputmode="numeric"
                pattern="[0-9]*"
                autocomplete="off"
                enterkeyhint="next"
                [ngModel]="documentNumber()"
                (ngModelChange)="onDocumentNumberChange($event)"
                (input)="onDocumentNumberInput($event)"
                (keydown)="onDocumentNumberKeyDown($event)"
                name="docNumber"
                placeholder="1020304050"
                required
                minlength="5"
                maxlength="20"
              />
            </div>

            <div class="form-group">
              <label for="birthDate">Fecha de nacimiento</label>
              <input
                id="birthDate"
                type="date"
                [max]="maxDate"
                enterkeyhint="next"
                [ngModel]="birthDate()"
                (ngModelChange)="birthDate.set($event)"
                name="birthDate"
                required
              />
              @if (isFutureDate()) {
                <small class="helper-text error-text">
                  La fecha de nacimiento no puede ser una fecha futura.
                </small>
              } @else if (calculatedAge(); as age) {
                <small class="helper-text" [class.error-text]="!isAgeValid()">
                  Edad: {{ age }} años
                  {{ isAgeValid() ? '(Rango asegurable 18-75)' : '(Fuera de rango asegurable)' }}
                </small>
              }
            </div>

            <div class="form-group">
              <label for="firstName">Nombres</label>
              <input
                id="firstName"
                type="text"
                autocomplete="given-name"
                enterkeyhint="next"
                [ngModel]="firstName()"
                (ngModelChange)="firstName.set($event)"
                name="firstName"
                placeholder="Carlos"
                required
                minlength="2"
              />
            </div>

            <div class="form-group">
              <label for="lastName">Apellidos</label>
              <input
                id="lastName"
                type="text"
                autocomplete="family-name"
                enterkeyhint="next"
                [ngModel]="lastName()"
                (ngModelChange)="lastName.set($event)"
                name="lastName"
                placeholder="Rodríguez"
                required
                minlength="2"
              />
            </div>

            <div class="form-group">
              <label for="phone">Teléfono celular</label>
              <input
                id="phone"
                type="tel"
                inputmode="tel"
                autocomplete="tel"
                enterkeyhint="next"
                [ngModel]="phone()"
                (ngModelChange)="phone.set($event)"
                name="phone"
                placeholder="3001234567"
                required
              />
            </div>

            <div class="form-group">
              <label for="email">Correo Electrónico</label>
              <input
                id="email"
                type="email"
                autocomplete="email"
                enterkeyhint="next"
                [ngModel]="email()"
                (ngModelChange)="email.set($event)"
                name="email"
                placeholder="carlos.rodriguez@email.com"
                required
              />
            </div>
          </div>
        </fieldset>

        <!-- Panel 2: Datos del Crédito / Riesgo -->
        <fieldset class="panel-section">
          <legend class="section-legend">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <rect x="2" y="5" width="20" height="14" rx="2" />
              <line x1="2" y1="10" x2="22" y2="10" />
            </svg>
            Datos del crédito y riesgo a asegurar
          </legend>

          <div class="fields-grid">
            <div class="form-group">
              <label for="financialEntity">Entidad financiera</label>
              <select
                id="financialEntity"
                [ngModel]="financialEntity()"
                (ngModelChange)="financialEntity.set($event)"
                name="financialEntity"
                required
              >
                <option value="Banco Unión">Banco Unión</option>
                <option value="Bancolombia">Bancolombia</option>
                <option value="Davivienda">Davivienda</option>
                <option value="Banco de Bogotá">Banco de Bogotá</option>
                <option value="BBVA Colombia">BBVA Colombia</option>
              </select>
            </div>

            <div class="form-group">
              <label for="city">Ciudad de residencia</label>
              <select
                id="city"
                [ngModel]="city()"
                (ngModelChange)="city.set($event)"
                name="city"
                required
              >
                <option value="Bogotá">Bogotá, D.C.</option>
                <option value="Medellín">Medellín</option>
                <option value="Cali">Cali</option>
                <option value="Barranquilla">Barranquilla</option>
                <option value="Bucaramanga">Bucaramanga</option>
              </select>
            </div>

            <div class="form-group">
              <label for="insuredAmount">Monto del préstamo / Suma asegurada</label>
              <input
                id="insuredAmount"
                type="number"
                step="5000000"
                min="10000000"
                enterkeyhint="next"
                [ngModel]="insuredAmount()"
                (ngModelChange)="insuredAmount.set(+$event)"
                name="insuredAmount"
                required
              />
              <small class="helper-text helper-money">
                <strong>{{ formattedAmount() }}</strong>
              </small>
            </div>

            <div class="form-row-group">
              <div class="form-group">
                <label for="termMonths">Plazo del crédito en meses</label>
                <input
                  id="termMonths"
                  type="number"
                  min="36"
                  max="360"
                  step="12"
                  enterkeyhint="next"
                  [ngModel]="termMonths()"
                  (ngModelChange)="termMonths.set(+$event)"
                  name="termMonths"
                  required
                />
                <small class="helper-text">
                  {{ termMonths() }} meses ({{ termMonths() / 12 | number: '1.0-1' }} años)
                </small>
              </div>

              <div class="form-group">
                <label for="occupationRisk">Nivel de riesgo ocupacional</label>
                <select
                  id="occupationRisk"
                  [ngModel]="occupationRisk()"
                  (ngModelChange)="occupationRisk.set(+$event)"
                  name="occupationRisk"
                  required
                >
                  <option [ngValue]="1">
                    Nivel 1 · Administrativo / Docencia / Oficina (Factor 1.0x)
                  </option>
                  <option [ngValue]="2">
                    Nivel 2 · Comercial / Ventas / Servicios (Factor 1.1x)
                  </option>
                  <option [ngValue]="3">
                    Nivel 3 · Técnico / Operativo / Manufactura (Factor 1.25x)
                  </option>
                  <option [ngValue]="4">
                    Nivel 4 · Transporte / Construcción / Seguridad (Factor 1.45x)
                  </option>
                  <option [ngValue]="5">
                    Nivel 5 · Alto Riesgo / Trabajo en Alturas / Minas (Factor 1.7x)
                  </option>
                </select>
              </div>
            </div>
          </div>
        </fieldset>

        @if (errorMessage()) {
          <div class="notice notice-error" role="alert">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <div>
              <strong>No es posible continuar con la cotización</strong>
              <p>{{ errorMessage() }}</p>
            </div>
          </div>
        }

        <div class="actions-row">
          <button type="submit" class="submit-button" [disabled]="validating() || !isFormValid()">
            @if (validating()) {
              <span class="spinner" aria-hidden="true"></span>
              Validando asegurabilidad...
            } @else {
              Validar y continuar &rarr;
            }
          </button>
        </div>
      </form>
    </section>
  `,
  styles: [
    `
      .step-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 24px;
      }
      .step-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 24px;
        gap: 16px;
      }
      .step-header h4 {
        margin: 0 0 6px;
        color: #0f172a;
        font-size: 1.25rem;
        font-weight: 700;
      }
      .subtitle {
        margin: 0;
        color: #64748b;
        font-size: 0.875rem;
        line-height: 1.5;
      }
      .chip {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #f1f5f9;
        color: #64748b;
        white-space: nowrap;
      }
      .chip.ok {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
      }
      .chip.error {
        background: #fef2f2;
        color: #b91c1c;
        border: 1px solid #fecaca;
      }
      .panel-section {
        border: 1px solid #f1f5f9;
        background: #f8fafc;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
      }
      .section-legend {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9375rem;
        font-weight: 700;
        color: #1e293b;
        padding: 0 8px;
      }
      .section-legend svg {
        color: #0b5474;
      }
      .fields-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
        margin-top: 12px;
      }
      .full-width {
        grid-column: 1 / -1;
      }
      .form-row-group {
        grid-column: 1 / -1;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      @media (max-width: 560px) {
        .form-row-group {
          grid-template-columns: 1fr;
        }
      }
      .form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .form-group label {
        font-size: 0.8125rem;
        font-weight: 600;
        color: #334155;
      }
      .form-group input,
      .form-group select {
        padding: 10px 14px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        font-size: 0.875rem;
        background: #ffffff;
        color: #0f172a;
        transition: border-color 0.15s ease;
        min-height: 42px;
        box-sizing: border-box;
      }
      .form-group input:focus,
      .form-group select:focus {
        outline: none;
        border-color: #0b5474;
        box-shadow: 0 0 0 3px rgba(11, 84, 116, 0.15);
      }
      .helper-text {
        font-size: 0.75rem;
        color: #64748b;
      }
      .helper-money {
        color: #0b5474;
      }
      .error-text {
        color: #b91c1c;
        font-weight: 600;
      }
      .notice {
        display: flex;
        gap: 12px;
        padding: 14px 18px;
        border-radius: 8px;
        font-size: 0.875rem;
        margin-bottom: 20px;
      }
      .notice.notice-error {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
      }
      .notice p {
        margin: 4px 0 0;
        font-size: 0.8125rem;
      }
      .actions-row {
        display: flex;
        justify-content: flex-end;
        margin-top: 20px;
      }
      .submit-button {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 12px 24px;
        background: #0b5474;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 0.9375rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.15s ease;
      }
      .submit-button:hover:not(:disabled) {
        background: #083c53;
      }
      .submit-button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-top-color: #ffffff;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
    `,
  ],
})
export class ClientDataStepComponent {
  private readonly clientService = inject(ClientService);

  readonly initialClient = input<ClientIdentification | null>(null);
  readonly initialRisk = input<RiskData | null>(null);

  readonly clientDataSubmitted = output<ClientQuoteSubmission>();

  // Titular Solicitante
  readonly documentType = linkedSignal(() => this.initialClient()?.document_type ?? 'CC');
  readonly documentNumber = linkedSignal(
    () => (this.initialClient()?.document_number ?? '1020304050').replace(/\D/g, ''),
  );
  readonly firstName = linkedSignal(() => this.initialClient()?.first_name ?? 'Carlos');
  readonly lastName = linkedSignal(() => this.initialClient()?.last_name ?? 'Rodríguez');
  readonly birthDate = linkedSignal(() => this.initialClient()?.birth_date ?? '1988-04-12');
  readonly phone = linkedSignal(() => this.initialClient()?.phone ?? '3001234567');
  readonly email = linkedSignal(() => this.initialClient()?.email ?? 'carlos.rodriguez@email.com');

  // Crédito Hipotecario / Riesgo
  readonly financialEntity = linkedSignal(
    () => this.initialRisk()?.financial_entity ?? 'Banco Unión',
  );
  readonly city = linkedSignal(() => this.initialRisk()?.city ?? 'Bogotá');
  readonly insuredAmount = linkedSignal(() => this.initialRisk()?.insured_amount ?? 150_000_000);
  readonly termMonths = linkedSignal(() => this.initialRisk()?.term_months ?? 240);
  readonly occupationRisk = linkedSignal(() => this.initialRisk()?.occupation_risk ?? 1);

  readonly validating = signal(false);
  readonly errorMessage = signal<string | null>(null);

  onDocumentNumberChange(val: string): void {
    const numeric = (val || '').replace(/\D/g, '');
    this.documentNumber.set(numeric);
  }

  onDocumentNumberInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const numeric = input.value.replace(/\D/g, '');
    if (input.value !== numeric) {
      input.value = numeric;
    }
    this.documentNumber.set(numeric);
  }

  onDocumentNumberKeyDown(event: KeyboardEvent): void {
    if (
      event.key === 'Backspace' ||
      event.key === 'Delete' ||
      event.key === 'Tab' ||
      event.key === 'Enter' ||
      event.key === 'ArrowLeft' ||
      event.key === 'ArrowRight' ||
      event.key === 'ArrowUp' ||
      event.key === 'ArrowDown' ||
      event.key === 'Home' ||
      event.key === 'End' ||
      event.ctrlKey ||
      event.metaKey
    ) {
      return;
    }
    if (!/^\d$/.test(event.key)) {
      event.preventDefault();
    }
  }

  readonly isDocumentNumberValid = computed(() => {
    const doc = this.documentNumber().trim();
    return doc.length >= 5 && doc.length <= 20 && /^\d+$/.test(doc);
  });

  readonly maxDate = (() => {
    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, '0');
    const d = String(today.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  })();

  readonly isFutureDate = computed(() => {
    const raw = this.birthDate();
    if (!raw) return false;
    const parts = raw.split('-');
    if (parts.length !== 3) return false;
    const birth = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    if (isNaN(birth.getTime())) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return birth.getTime() > today.getTime();
  });

  readonly calculatedAge = computed(() => {
    const raw = this.birthDate();
    if (!raw) return null;
    const parts = raw.split('-');
    if (parts.length !== 3) return null;
    const birth = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    if (isNaN(birth.getTime())) return null;
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  });

  readonly isAgeValid = computed(() => {
    if (this.isFutureDate()) return false;
    const age = this.calculatedAge();
    return age !== null && age >= 18 && age <= 75;
  });

  readonly formattedAmount = computed(() => COP.format(this.insuredAmount() || 0));

  readonly isFormValid = computed(() => {
    return (
      this.isDocumentNumberValid() &&
      !this.isFutureDate() &&
      this.isAgeValid() &&
      this.firstName().trim().length >= 2 &&
      this.lastName().trim().length >= 2 &&
      this.phone().trim().length >= 7 &&
      this.email().includes('@') &&
      this.insuredAmount() > 0 &&
      this.termMonths() >= 36
    );
  });

  onSubmit(): void {
    if (!this.isFormValid()) {
      if (!this.isDocumentNumberValid()) {
        this.errorMessage.set(
          'El número de documento solo debe contener dígitos numéricos (entre 5 y 20 dígitos).',
        );
      } else if (this.isFutureDate()) {
        this.errorMessage.set('La fecha de nacimiento no puede ser una fecha futura.');
      } else if (!this.isAgeValid()) {
        this.errorMessage.set(
          `El solicitante tiene ${this.calculatedAge()} años. Debe tener entre 18 y 75 años para ser asegurable.`,
        );
      } else {
        this.errorMessage.set('Por favor complete todos los campos obligatorios del formulario.');
      }
      return;
    }

    this.validating.set(true);
    this.errorMessage.set(null);

    const clientPayload: ClientIdentification = {
      document_type: this.documentType(),
      document_number: this.documentNumber().trim(),
      first_name: this.firstName().trim(),
      last_name: this.lastName().trim(),
      birth_date: this.birthDate(),
      email: this.email().trim(),
      phone: this.phone().trim(),
    };

    const riskPayload: RiskData = {
      financial_entity: this.financialEntity(),
      insured_amount: this.insuredAmount(),
      term_months: this.termMonths(),
      occupation_risk: this.occupationRisk(),
      city: this.city(),
    };

    this.clientService
      .validateClient(clientPayload)
      .pipe(finalize(() => this.validating.set(false)))
      .subscribe({
        next: () => {
          this.clientDataSubmitted.emit({
            client: clientPayload,
            risk: riskPayload,
          });
        },
        error: (err: HttpErrorResponse) => {
          const detail = err.error?.detail || 'Error al validar la asegurabilidad del cliente.';
          this.errorMessage.set(detail);
        },
      });
  }
}

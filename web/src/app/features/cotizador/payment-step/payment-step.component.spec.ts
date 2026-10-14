import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { PaymentReceipt } from '../../../core/models/payment.model';
import { PolicyRecord } from '../../../core/models/policy.model';
import { PaymentStepComponent } from './payment-step.component';

const COP = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
});
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const DECLINED = 'Pago rechazado: fondos insuficientes. Intente con otro medio de pago.';

describe('PaymentStepComponent (HU-WEB-06)', () => {
  const policy: PolicyRecord = {
    policy_number: 'POL-2026-00001',
    quote_id: 'QUO-1',
    insured_document: '1020304050',
    conditions: {
      tier: 'standard',
      monthly_premium: 27_360,
      annual_premium: 328_320,
      coverages: [],
      breakdown: [],
    },
    status: 'ISSUED',
    issued_at: '2026-10-11T12:00:00Z',
    valid_until: '2027-10-11T12:00:00Z',
  };
  const receipt: PaymentReceipt = {
    transaction_id: 'TX-1',
    idempotency_key: 'clave',
    policy_number: 'POL-2026-00001',
    amount: 27_360,
    status: 'APPROVED',
    receipt_number: 'REC-2026-00001',
    created_at: '2026-10-11T12:05:00Z',
  };
  let fixture: ComponentFixture<PaymentStepComponent>;
  let http: HttpTestingController;
  const page = () => fixture.nativeElement as HTMLElement;
  const shownKey = () => page().querySelector('code')?.textContent;
  const payButton = () => page().querySelector<HTMLButtonElement>('.pay-button');
  const alert = () => page().querySelector('[role="alert"]')?.textContent?.trim();
  const choose = (label: string) => {
    [...page().querySelectorAll('label')]
      .find((option) => option.textContent?.includes(label))!
      .querySelector('input')!
      .click();
    fixture.detectChanges();
  };
  const pay = () => {
    payButton()!.click();
    fixture.detectChanges();
    return http.expectOne('/api/v1/experience/payments/charge');
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [PaymentStepComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    fixture = TestBed.createComponent(PaymentStepComponent);
    fixture.componentRef.setInput('policy', policy);
    fixture.detectChanges();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('cobra la prima una sola vez con la clave que muestra y confirma el recibo', () => {
    const key = shownKey();
    expect(payButton()!.textContent?.trim()).toBe(`Pagar ${COP.format(27_360)}`);

    payButton()!.click();
    fixture.detectChanges();
    const call = pay();

    expect(key).toMatch(UUID_V4);
    expect(call.request.headers.get('Idempotency-Key')).toBe(key);
    expect(call.request.body).toEqual({
      policy_number: 'POL-2026-00001',
      amount: 27_360,
      payment_method: 'PSE',
      token_or_account: 'tok_pse_bancolombia',
    });
    call.flush(receipt);
    fixture.detectChanges();
    expect(page().querySelector('[role="status"]')?.textContent?.replace(/\s+/g, ' ')).toContain(
      'Pago aprobado · recibo REC-2026-00001',
    );
    expect(payButton()).toBeNull();
  });

  it('si el banco rechaza muestra el motivo; otro medio de pago usa otra clave y limpia el aviso', () => {
    choose('cuenta sin fondos');
    const declinedKey = shownKey();

    const call = pay();
    expect(call.request.body.token_or_account).toBe('tok_insufficient_funds');
    call.flush({ detail: DECLINED }, { status: 402, statusText: 'Payment Required' });
    fixture.detectChanges();

    expect(alert()).toBe(DECLINED);
    expect(payButton()!.disabled).toBe(false);
    choose('Tarjeta terminada en 4417');
    expect(alert()).toBeUndefined();
    expect(shownKey()).not.toBe(declinedKey);
  });

  it('sin respuesta pide reintentar y el reintento usa la misma clave', () => {
    const first = pay();
    first.error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect(alert()).toContain('No se pudo confirmar el pago');
    const retry = pay();
    expect(retry.request.headers.get('Idempotency-Key')).toBe(
      first.request.headers.get('Idempotency-Key'),
    );
    retry.flush(receipt);
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { PolicyRecord } from '../../core/models/policy.model';
import { QuoteResponse, QuoteTier } from '../../core/models/quote.model';
import { CotizadorComponent } from './cotizador.component';

describe('CotizadorComponent (Flujo Comercial HU-WEB-01 a HU-WEB-06)', () => {
  let component: CotizadorComponent;
  let fixture: ComponentFixture<CotizadorComponent>;
  let http: HttpTestingController;

  const tier = (name: QuoteTier['tier'], premium: number): QuoteTier => ({
    tier: name,
    monthly_premium: premium,
    annual_premium: premium * 12,
    coverages: [],
    breakdown: [{ code: 'base_rate', label: 'Tarifa base actuarial', multiplier: 1, amount: premium }],
  });

  const quote: QuoteResponse = {
    quote_id: 'QUO-1',
    document_number: '1020304050',
    status: 'active',
    score_applied: 700,
    tiers: [tier('basic', 20_000), tier('standard', 27_000), tier('premium', 36_000)],
    created_at: '2026-10-09T00:00:00Z',
    expires_at: '2026-10-24T00:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CotizadorComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(CotizadorComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('debe crearse el componente del cotizador', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar el título del cotizador', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Cotizador de Seguros de Vida');
  });

  it('debe mostrar las etapas del proceso comercial e iniciar activo en el paso 1', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const steps = compiled.querySelectorAll('.step');
    expect(steps.length).toBe(5);
    expect(steps[0].classList.contains('active')).toBe(true);
    expect(steps[1].classList.contains('active')).toBe(false);
  });

  describe('captura de datos y solicitud de cotización (HU-WEB-02)', () => {
    it('renderiza el paso 1 de identificación y oculta consentimiento inicialmente', () => {
      const step1 = fixture.nativeElement.querySelector('app-client-data-step');
      expect(step1).not.toBeNull();
      expect(fixture.nativeElement.querySelector('app-consent-step')).toBeNull();
    });

    it('actualiza los datos del cliente y avanza a consentimiento al recibir clientDataSubmitted', () => {
      const submission = {
        client: {
          document_type: 'CC',
          document_number: '1020304050',
          first_name: 'Carlos',
          last_name: 'Rodríguez',
          birth_date: '1988-04-12',
          email: 'carlos@correo.co',
          phone: '3001234567',
        },
        risk: {
          financial_entity: 'Banco Unión',
          insured_amount: 150_000_000,
          term_months: 240,
          occupation_risk: 1,
          city: 'Bogotá',
        },
      };

      component.onClientDataSubmitted(submission);
      fixture.detectChanges();

      expect(component.client()).toEqual(submission.client);
      expect(component.risk()).toEqual(submission.risk);
      expect(component.currentStep()).toBe(2);
      const steps = fixture.nativeElement.querySelectorAll('.step');
      expect(steps[0].classList.contains('completed')).toBe(true);
      expect(steps[1].classList.contains('active')).toBe(true);
      expect(fixture.nativeElement.querySelector('app-client-data-step')).toBeNull();
      expect(fixture.nativeElement.querySelector('app-consent-step')).not.toBeNull();
    });

    it('solicita la cotización usando los datos capturados y carga los planes', () => {
      component.client.set({
        document_type: 'CC',
        document_number: '1020304050',
        first_name: 'Carlos',
        last_name: 'Rodríguez',
        birth_date: '1988-04-12',
        email: 'carlos@correo.co',
        phone: '3001234567',
      });
      component.risk.set({
        financial_entity: 'Davivienda',
        insured_amount: 200_000_000,
        term_months: 180,
        occupation_risk: 2,
        city: 'Medellín',
      });

      component.requestQuote();

      const call = http.expectOne('/api/v1/experience/quotes');
      expect(call.request.method).toBe('POST');
      expect(call.request.body).toEqual({
        document_type: 'CC',
        document_number: '1020304050',
        birth_date: '1988-04-12',
        insured_amount: 200_000_000,
        city: 'Medellín',
        occupation_risk: 2,
      });

      call.flush(quote);
      fixture.detectChanges();

      expect(component.quote()).toEqual(quote);
      expect(fixture.nativeElement.querySelector('app-premium-breakdown')).not.toBeNull();
    });
  });

  describe('consentimiento Open Finance (HU-WEB-01)', () => {
    it('no muestra consentimiento en paso 1 y lo renderiza al avanzar al paso 2', () => {
      expect(fixture.nativeElement.querySelector('app-consent-step')).toBeNull();
      component.currentStep.set(2);
      fixture.detectChanges();
      const consentStep = fixture.nativeElement.querySelector('app-consent-step');
      expect(consentStep).not.toBeNull();
    });

    it('actualiza el estado de consentimiento y dispara la cotización', () => {
      component.currentStep.set(2);
      fixture.detectChanges();
      const mockRecord = {
        consent_id: 'CNS-TEST-123',
        document_number: '1020304050',
        channel: 'web',
        purpose: 'Test',
        scope: 'Test',
        validity_days: 30,
        status: 'GRANTED' as const,
        consent_hash: '1234567890abcdef',
        granted_at: '2026-10-13T00:00:00Z',
        expires_at: '2026-11-12T00:00:00Z',
      };

      component.onConsentGranted(mockRecord);
      const quoteCall = http.expectOne('/api/v1/experience/quotes');
      quoteCall.flush(quote);
      fixture.detectChanges();

      expect(component.consent()).toEqual(mockRecord);
      const steps = fixture.nativeElement.querySelectorAll('.step');
      expect(steps[1].classList.contains('completed')).toBe(true);
    });
  });

  describe('desglose de la prima (HU-WEB-03)', () => {
    const total = () => (fixture.nativeElement as HTMLElement).querySelector('[data-testid="total"]')?.textContent;

    it('no muestra el desglose sin cotización', () => {
      expect((fixture.nativeElement as HTMLElement).querySelector('app-premium-breakdown')).toBeNull();
    });

    it('muestra el desglose del plan estándar por defecto', () => {
      component.quote.set(quote);
      fixture.detectChanges();

      expect(total()).toContain('27.000');
    });

    it('cambia el desglose al elegir otro plan', () => {
      component.quote.set(quote);
      fixture.detectChanges();

      const tabs = (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>('.tier-tab');
      tabs[2].click();
      fixture.detectChanges();

      expect(total()).toContain('36.000');
      expect(tabs[2].getAttribute('aria-selected')).toBe('true');
    });
  });

  describe('perfil parcial (HU-WEB-04)', () => {
    const banner = () => (fixture.nativeElement as HTMLElement).querySelector('[role="alert"]');

    it('no muestra el aviso con una cotización completa', () => {
      component.quote.set(quote);
      fixture.detectChanges();

      expect(banner()).toBeNull();
    });

    it('avisa que la cotización degradada usa perfil parcial y puede reajustarse', () => {
      component.quote.set({ ...quote, status: 'degraded', degradation_reason: 'TIMEOUT_EXCEEDED' });
      fixture.detectChanges();

      expect(banner()?.textContent).toContain('Cotización calculada con perfil parcial por latencia en proveedores de scoring');
      expect(banner()?.textContent).toContain('podrá reajustarse');
    });
  });

  describe('emisión de la póliza (HU-WEB-05)', () => {
    const policy: PolicyRecord = {
      policy_number: 'POL-2026-00001',
      quote_id: 'QUO-1',
      insured_document: '1020304050',
      conditions: tier('premium', 36_000),
      status: 'ISSUED',
      issued_at: '2026-10-11T12:00:00Z',
      valid_until: '2027-10-11T12:00:00Z',
    };
    const page = () => fixture.nativeElement as HTMLElement;
    const button = (label: string) =>
      [...page().querySelectorAll('button')].find((candidate) => candidate.textContent?.trim() === label);
    const issue = () => {
      button('Emitir póliza')!.click();
      fixture.detectChanges();
      return http.expectOne('/api/v1/experience/policies');
    };

    beforeEach(() => {
      component.quote.set(quote);
      fixture.detectChanges();
    });

    it('emite el plan elegido y confirma el número y la vigencia', () => {
      component.selectedTier.set('premium');
      fixture.detectChanges();

      const call = issue();
      expect(call.request.body).toEqual({ quote_id: 'QUO-1', tier: 'premium' });
      expect(button('Emitir póliza')!.disabled).toBe(true);
      call.flush(policy);
      fixture.detectChanges();

      expect(page().querySelector('[role="status"]')?.textContent?.replace(/\s+/g, ' ')).toContain(
        'Póliza emitida POL-2026-00001 Plan Premium · vigente del 11/10/2026 al 11/10/2027',
      );
      expect(button('Emitir póliza')).toBeUndefined();
      expect(page().querySelector('app-payment-step')).not.toBeNull();
    });

    it('si la cotización venció pide recotizar, y recotizar limpia la cotización', () => {
      issue().flush({ detail: 'La cotización venció' }, { status: 409, statusText: 'Conflict' });
      fixture.detectChanges();

      expect(page().querySelector('[role="alert"]')?.textContent).toContain('La cotización venció');
      expect(button('Emitir póliza')).toBeUndefined();
      button('Recotizar con datos actuales')!.click();
      fixture.detectChanges();
      expect(page().querySelector('[role="tablist"]')).toBeNull();

      const quoteCall = http.expectOne('/api/v1/experience/quotes');
      quoteCall.flush(quote);
    });

    it('ante otra falla avisa y deja reintentar', () => {
      issue().flush(null, { status: 500, statusText: 'Internal Server Error' });
      fixture.detectChanges();

      expect(page().querySelector('[role="alert"]')?.textContent).toContain('No se pudo emitir la póliza');
      expect(button('Recotizar con datos actuales')).toBeUndefined();
      expect(button('Emitir póliza')!.disabled).toBe(false);
    });

    it('una cotización nueva descarta la póliza emitida', () => {
      issue().flush(policy);
      component.quote.set({ ...quote, quote_id: 'QUO-2' });
      fixture.detectChanges();

      expect(page().querySelector('[role="status"]')).toBeNull();
      expect(button('Emitir póliza')).toBeDefined();
    });
  });
});

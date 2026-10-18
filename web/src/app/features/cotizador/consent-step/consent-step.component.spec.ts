import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ConsentRecord } from '../../../core/models/consent.model';
import { ConsentStepComponent } from './consent-step.component';

describe('ConsentStepComponent (HU-WEB-01)', () => {
  let component: ConsentStepComponent;
  let fixture: ComponentFixture<ConsentStepComponent>;
  let http: HttpTestingController;

  const mockRecord: ConsentRecord = {
    consent_id: 'CNS-A1B2C3D4E5F6',
    document_number: '1020304050',
    channel: 'web',
    purpose: 'Perfilamiento y cotización de seguro de vida hipotecario con Open Finance',
    scope: 'Historial crediticio, capacidad de endeudamiento y scoring financiero',
    validity_days: 30,
    status: 'GRANTED',
    consent_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    granted_at: '2026-10-13T20:00:00Z',
    expires_at: '2026-11-12T20:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConsentStepComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(ConsentStepComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('debe crearse el componente de consentimiento', () => {
    expect(component).toBeTruthy();
  });

  it('el botón de registro debe estar deshabilitado mientras no se acepten los términos o el OTP sea inválido', () => {
    const button = fixture.nativeElement.querySelector('.submit-button') as HTMLButtonElement;
    expect(button.disabled).toBe(true);

    // Con términos aceptados pero OTP vacío sigue deshabilitado
    component.termsAccepted.set(true);
    fixture.detectChanges();
    expect(button.disabled).toBe(true);

    // Con términos y OTP válido de 6 dígitos se habilita
    component.otpCode.set('839201');
    fixture.detectChanges();
    expect(button.disabled).toBe(false);
  });

  it('registra el consentimiento exitosamente y muestra el hash SHA-256', () => {
    component.termsAccepted.set(true);
    component.otpCode.set('839201');
    fixture.detectChanges();

    let emittedRecord: ConsentRecord | undefined;
    component.consentGranted.subscribe((rec) => (emittedRecord = rec));

    const button = fixture.nativeElement.querySelector('.submit-button') as HTMLButtonElement;
    button.click();

    const call = http.expectOne('/api/v1/experience/consent');
    expect(call.request.method).toBe('POST');
    expect(call.request.body.document_number).toBe('1020304050');
    expect(call.request.body.terms_accepted).toBe(true);
    expect(call.request.body.otp_code).toBe('839201');

    call.flush(mockRecord);
    fixture.detectChanges();

    expect(emittedRecord?.consent_id).toBe('CNS-A1B2C3D4E5F6');
    const hashEl = fixture.nativeElement.querySelector('[data-testid="consent-hash"]');
    expect(hashEl?.textContent).toContain('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
    expect(fixture.nativeElement.textContent).toContain('Consentimiento registrado');
  });

  it('muestra mensaje de error si el registro de consentimiento falla', () => {
    component.termsAccepted.set(true);
    component.otpCode.set('839201');
    fixture.detectChanges();

    component.submitConsent();

    const call = http.expectOne('/api/v1/experience/consent');
    call.flush({ detail: 'Código OTP de verificación incorrecto o expirado.' }, { status: 400, statusText: 'Bad Request' });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Código OTP de verificación incorrecto o expirado.');
  });

  it('sincroniza docNumber reactivamente cuando cambia el input documentNumber', () => {
    expect(component.docNumber()).toBe('1020304050');

    fixture.componentRef.setInput('documentNumber', '52194832');
    fixture.detectChanges();

    expect(component.docNumber()).toBe('52194832');
  });

  it('el botón de registro permanece deshabilitado si el código OTP no es numérico de 6 dígitos', () => {
    component.termsAccepted.set(true);

    component.otpCode.set('abcdef');
    fixture.detectChanges();
    const button = fixture.nativeElement.querySelector('.submit-button') as HTMLButtonElement;
    expect(button.disabled).toBe(true);

    component.otpCode.set('12345');
    fixture.detectChanges();
    expect(button.disabled).toBe(true);

    component.otpCode.set('839201');
    fixture.detectChanges();
    expect(button.disabled).toBe(false);
  });

  it('envía finalidad, alcance y vigencia personalizados indicados por el asesor', () => {
    component.termsAccepted.set(true);
    component.otpCode.set('839201');
    component.purpose.set('Finalidad personalizada de suscripción');
    component.scope.set('Historial crediticio y bancario ampliado');
    component.validityDays.set(60);
    fixture.detectChanges();

    component.submitConsent();

    const call = http.expectOne('/api/v1/experience/consent');
    expect(call.request.body.purpose).toBe('Finalidad personalizada de suscripción');
    expect(call.request.body.scope).toBe('Historial crediticio y bancario ampliado');
    expect(call.request.body.validity_days).toBe(60);
    call.flush(mockRecord);
  });

  it('renderiza la vigencia dinámicamente en el panel informativo según validityDays', () => {
    component.validityDays.set(90);
    fixture.detectChanges();

    const infoGrid = fixture.nativeElement.querySelector('.info-grid');
    expect(infoGrid?.textContent).toContain('90 días calendario a partir del momento de la autorización.');
  });
});


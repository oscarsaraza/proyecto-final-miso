import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ClientDataStepComponent } from './client-data-step.component';
import { ClientIdentification, ClientQuoteSubmission, RiskData } from '../../../core/models/client.model';

describe('ClientDataStepComponent (HU-WEB-02 / TC-S1-03)', () => {
  let component: ClientDataStepComponent;
  let fixture: ComponentFixture<ClientDataStepComponent>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ClientDataStepComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(ClientDataStepComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('debe crearse el componente del paso de captura de datos del cliente', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar los paneles de datos del titular y de crédito hipotecario', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('#step1-title')?.textContent).toContain('Paso 1: Identificación');
    expect(el.querySelector('#docNumber')).not.toBeNull();
    expect(el.querySelector('#insuredAmount')).not.toBeNull();
    expect(el.querySelector('#financialEntity')).not.toBeNull();
  });

  it('debe calcular la edad y el estado de elegibilidad a partir de la fecha de nacimiento', () => {
    // Fecha de nacimiento para ~38 años
    component.birthDate.set('1988-04-12');
    fixture.detectChanges();

    expect(component.calculatedAge()).toBeGreaterThanOrEqual(18);
    expect(component.calculatedAge()).toBeLessThanOrEqual(75);
    expect(component.isAgeValid()).toBe(true);

    // Fecha de nacimiento para menor de edad (10 años)
    component.birthDate.set('2016-01-01');
    fixture.detectChanges();

    expect(component.isAgeValid()).toBe(false);
    expect(component.isFormValid()).toBe(false);

    // Fecha de nacimiento para mayor de 75 años (86 años)
    component.birthDate.set('1940-01-01');
    fixture.detectChanges();

    expect(component.isAgeValid()).toBe(false);
    expect(component.isFormValid()).toBe(false);
  });

  it('no debe permitir fechas de nacimiento futuras', () => {
    const inputEl = fixture.nativeElement.querySelector('#birthDate') as HTMLInputElement;
    expect(inputEl.max).toBe(component.maxDate);

    component.birthDate.set('2099-01-01');
    fixture.detectChanges();

    expect(component.isFutureDate()).toBe(true);
    expect(component.isAgeValid()).toBe(false);
    expect(component.isFormValid()).toBe(false);

    const helperEl = fixture.nativeElement.querySelector('.error-text');
    expect(helperEl?.textContent).toContain('La fecha de nacimiento no puede ser una fecha futura');

    component.onSubmit();
    fixture.detectChanges();
    expect(component.errorMessage()).toContain('La fecha de nacimiento no puede ser una fecha futura');
  });

  it('debe formatear el monto asegurado en pesos colombianos COP', () => {
    component.insuredAmount.set(200_000_000);
    fixture.detectChanges();

    expect(component.formattedAmount()).toContain('200.000.000');
  });

  it('debe validar con ClientService y emitir clientDataSubmitted al completar con éxito', () => {
    let emitted: ClientQuoteSubmission | undefined;
    component.clientDataSubmitted.subscribe((data) => (emitted = data));

    component.documentNumber.set('1020304050');
    component.firstName.set('Carlos');
    component.lastName.set('Rodríguez');
    component.birthDate.set('1988-04-12');
    component.phone.set('3001234567');
    component.email.set('carlos@correo.co');
    component.insuredAmount.set(180_000_000);
    component.financialEntity.set('Banco Unión');
    component.termMonths.set(240);
    component.occupationRisk.set(2);
    component.city.set('Medellín');
    fixture.detectChanges();

    component.onSubmit();

    const call = http.expectOne('/api/v1/experience/clients/validate');
    expect(call.request.method).toBe('POST');
    expect(call.request.body.document_number).toBe('1020304050');
    expect(call.request.body.birth_date).toBe('1988-04-12');

    call.flush({ status: 'ELIGIBLE', age: 38 });

    expect(emitted).toBeDefined();
    expect(emitted?.client.document_number).toBe('1020304050');
    expect(emitted?.risk.insured_amount).toBe(180_000_000);
    expect(emitted?.risk.financial_entity).toBe('Banco Unión');
  });

  it('debe mostrar mensaje de error si el BFF rechaza la asegurabilidad por edad', () => {
    component.onSubmit();

    const call = http.expectOne('/api/v1/experience/clients/validate');
    call.flush(
      { detail: 'El solicitante tiene 17 años. Debe tener entre 18 y 75 años para ser asegurable.' },
      { status: 400, statusText: 'Bad Request' }
    );
    fixture.detectChanges();

    expect(component.errorMessage()).toContain('17 años');
    const alert = fixture.nativeElement.querySelector('.notice.notice-error');
    expect(alert).not.toBeNull();
    expect(alert?.textContent).toContain('17 años');
  });

  it('debe inicializarse con datos iniciales si se suministran', () => {
    const initialClient: ClientIdentification = {
      document_type: 'CE',
      document_number: '987654321',
      first_name: 'Ana',
      last_name: 'Gómez',
      birth_date: '1992-08-25',
      email: 'ana.gomez@test.com',
      phone: '3109876543',
    };
    const initialRisk: RiskData = {
      financial_entity: 'Davivienda',
      insured_amount: 250_000_000,
      term_months: 180,
      occupation_risk: 3,
      city: 'Cali',
    };

    fixture.componentRef.setInput('initialClient', initialClient);
    fixture.componentRef.setInput('initialRisk', initialRisk);
    fixture.detectChanges();

    expect(component.documentType()).toBe('CE');
    expect(component.documentNumber()).toBe('987654321');
    expect(component.firstName()).toBe('Ana');
    expect(component.financialEntity()).toBe('Davivienda');
    expect(component.insuredAmount()).toBe(250_000_000);
  });

  it('solo debe permitir valores numéricos en el número de documento', () => {
    component.onDocumentNumberChange('1020abc3040');
    expect(component.documentNumber()).toBe('10203040');

    const inputEl = fixture.nativeElement.querySelector('#docNumber') as HTMLInputElement;
    inputEl.value = '52A.194-832';
    const inputEvent = new Event('input');
    Object.defineProperty(inputEvent, 'target', { value: inputEl });
    component.onDocumentNumberInput(inputEvent);

    expect(inputEl.value).toBe('52194832');
    expect(component.documentNumber()).toBe('52194832');

    const letterEvent = new KeyboardEvent('keydown', { key: 'a', cancelable: true });
    component.onDocumentNumberKeyDown(letterEvent);
    expect(letterEvent.defaultPrevented).toBe(true);

    const digitEvent = new KeyboardEvent('keydown', { key: '5', cancelable: true });
    component.onDocumentNumberKeyDown(digitEvent);
    expect(digitEvent.defaultPrevented).toBe(false);

    const controlEvent = new KeyboardEvent('keydown', { key: 'Backspace', cancelable: true });
    component.onDocumentNumberKeyDown(controlEvent);
    expect(controlEvent.defaultPrevented).toBe(false);
  });

  it('invalida el formulario y muestra error si el documento tiene menos de 5 dígitos o está vacío', () => {
    component.documentNumber.set('123');
    fixture.detectChanges();

    expect(component.isDocumentNumberValid()).toBe(false);
    expect(component.isFormValid()).toBe(false);

    component.onSubmit();
    fixture.detectChanges();

    expect(component.errorMessage()).toContain('dígitos numéricos');
  });
});


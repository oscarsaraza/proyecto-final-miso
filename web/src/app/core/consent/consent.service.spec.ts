import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ConsentRecord, ConsentRequest } from '../models/consent.model';
import { ConsentService } from './consent.service';

describe('ConsentService', () => {
  let service: ConsentService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ConsentService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('registra el consentimiento en el BFF de experiencia (HU-WEB-01)', () => {
    const request: ConsentRequest = {
      document_number: '1020304050',
      channel: 'web',
      otp_code: '839201',
      terms_accepted: true,
      purpose: 'Perfilamiento con Open Finance',
      scope: 'Historial crediticio',
      validity_days: 30,
    };
    let received: ConsentRecord | undefined;

    service.registerConsent(request).subscribe((record) => (received = record));

    const call = http.expectOne('/api/v1/experience/consent');
    expect(call.request.method).toBe('POST');
    expect(call.request.body).toEqual(request);

    const mockResponse: ConsentRecord = {
      consent_id: 'CNS-A1B2C3D4E5F6',
      document_number: '1020304050',
      channel: 'web',
      purpose: 'Perfilamiento con Open Finance',
      scope: 'Historial crediticio',
      validity_days: 30,
      status: 'GRANTED',
      consent_hash: 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
      granted_at: '2026-10-13T20:00:00Z',
      expires_at: '2026-11-12T20:00:00Z',
    };
    call.flush(mockResponse);

    expect(received?.consent_id).toBe('CNS-A1B2C3D4E5F6');
    expect(received?.status).toBe('GRANTED');
    expect(received?.consent_hash).toBe(mockResponse.consent_hash);
  });

  it('consulta el consentimiento vigente por documento', () => {
    let received: ConsentRecord | undefined;

    service.getConsent('1020304050').subscribe((record) => (received = record));

    const call = http.expectOne('/api/v1/experience/consent/1020304050');
    expect(call.request.method).toBe('GET');
    call.flush({ consent_id: 'CNS-A1', document_number: '1020304050', status: 'GRANTED' });

    expect(received?.consent_id).toBe('CNS-A1');
  });
});

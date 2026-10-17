import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ClientIdentification, ClientValidationResponse } from '../models/client.model';
import { ClientService } from './client.service';

describe('ClientService (HU-WEB-02 / TC-S1-03)', () => {
  let service: ClientService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ClientService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('valida la asegurabilidad del cliente en el BFF de experiencia', () => {
    const client: ClientIdentification = {
      document_type: 'CC',
      document_number: '1020304050',
      first_name: 'Carlos',
      last_name: 'Rodriguez',
      birth_date: '1988-04-12',
      email: 'carlos.rodriguez@email.com',
      phone: '3001234567',
    };
    let received: ClientValidationResponse | undefined;

    service.validateClient(client).subscribe((res) => (received = res));

    const call = http.expectOne('/api/v1/experience/clients/validate');
    expect(call.request.method).toBe('POST');
    expect(call.request.body).toEqual(client);

    const mockResponse: ClientValidationResponse = {
      status: 'ELIGIBLE',
      age: 38,
    };
    call.flush(mockResponse);

    expect(received?.status).toBe('ELIGIBLE');
    expect(received?.age).toBe(38);
  });
});

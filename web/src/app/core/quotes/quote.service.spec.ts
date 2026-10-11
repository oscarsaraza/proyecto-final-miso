import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { QuoteRequest, QuoteResponse } from '../models/quote.model';
import { QuoteService } from './quote.service';

describe('QuoteService', () => {
  let service: QuoteService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(QuoteService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('solicita la cotización al BFF de experiencia', () => {
    const request: QuoteRequest = {
      document_type: 'CC',
      document_number: '1020304050',
      birth_date: '1990-05-15',
      insured_amount: 100_000_000,
    };
    let received: QuoteResponse | undefined;

    service.createQuote(request).subscribe((quote) => (received = quote));

    const call = http.expectOne('/api/v1/experience/quotes');
    expect(call.request.method).toBe('POST');
    expect(call.request.body).toEqual(request);
    call.flush({ quote_id: 'QUO-1', tiers: [] });
    expect(received?.quote_id).toBe('QUO-1');
  });
});

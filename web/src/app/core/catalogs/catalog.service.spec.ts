import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { City, FinancialEntity } from '../models/catalog.model';
import { CatalogService } from './catalog.service';

describe('CatalogService (HU-WEB-02.1)', () => {
  let service: CatalogService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CatalogService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('consulta las entidades financieras desde el BFF de experiencia', () => {
    const mockEntities: FinancialEntity[] = [
      { id: 1, code: 'BANCO_UNION', name: 'Banco Unión', is_active: true },
      { id: 2, code: 'BANCOLOMBIA', name: 'Bancolombia', is_active: true },
    ];
    let received: FinancialEntity[] | undefined;

    service.getFinancialEntities().subscribe((data) => (received = data));

    const call = http.expectOne('/api/v1/experience/catalogs/financial-entities');
    expect(call.request.method).toBe('GET');

    call.flush(mockEntities);
    expect(received).toEqual(mockEntities);
  });

  it('consulta las ciudades desde el BFF de experiencia', () => {
    const mockCities: City[] = [
      { id: 1, code: 'BOGOTA', name: 'Bogotá, D.C.', is_active: true },
      { id: 2, code: 'MEDELLIN', name: 'Medellín', is_active: true },
    ];
    let received: City[] | undefined;

    service.getCities().subscribe((data) => (received = data));

    const call = http.expectOne('/api/v1/experience/catalogs/cities');
    expect(call.request.method).toBe('GET');

    call.flush(mockCities);
    expect(received).toEqual(mockCities);
  });
});


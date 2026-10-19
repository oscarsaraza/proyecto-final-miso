import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { City, FinancialEntity } from '../models/catalog.model';
import { API_BASE_URL } from '../quotes/quote.service';

/** Servicio de consulta de catálogos dinámicos (HU-WEB-02.1) */
@Injectable({
  providedIn: 'root',
})
export class CatalogService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  getFinancialEntities(): Observable<FinancialEntity[]> {
    return this.http.get<FinancialEntity[]>(`${this.baseUrl}/experience/catalogs/financial-entities`);
  }

  getCities(): Observable<City[]> {
    return this.http.get<City[]>(`${this.baseUrl}/experience/catalogs/cities`);
  }
}


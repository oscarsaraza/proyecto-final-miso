import { HttpClient } from '@angular/common/http';
import { Injectable, InjectionToken, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { QuoteRequest, QuoteResponse } from '../models/quote.model';

export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => '/api/v1',
});

@Injectable({
  providedIn: 'root',
})
export class QuoteService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  createQuote(request: QuoteRequest): Observable<QuoteResponse> {
    return this.http.post<QuoteResponse>(`${this.baseUrl}/experience/quotes`, request);
  }
}

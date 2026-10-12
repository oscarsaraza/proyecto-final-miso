import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { PaymentChargeRequest, PaymentReceipt } from '../models/payment.model';
import { API_BASE_URL } from '../quotes/quote.service';

@Injectable({
  providedIn: 'root',
})
export class PaymentService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  charge(request: PaymentChargeRequest, idempotencyKey: string): Observable<PaymentReceipt> {
    return this.http.post<PaymentReceipt>(`${this.baseUrl}/experience/payments/charge`, request, {
      headers: { 'Idempotency-Key': idempotencyKey },
    });
  }
}

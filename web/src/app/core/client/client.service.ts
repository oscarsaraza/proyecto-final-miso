import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ClientIdentification, ClientValidationResponse } from '../models/client.model';
import { API_BASE_URL } from '../quotes/quote.service';

@Injectable({
  providedIn: 'root',
})
export class ClientService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  validateClient(client: ClientIdentification): Observable<ClientValidationResponse> {
    return this.http.post<ClientValidationResponse>(`${this.baseUrl}/experience/clients/validate`, client);
  }
}

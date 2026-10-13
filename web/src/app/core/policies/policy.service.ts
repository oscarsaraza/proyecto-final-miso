import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { PolicyIssueRequest, PolicyRecord } from '../models/policy.model';
import { API_BASE_URL } from '../quotes/quote.service';

@Injectable({
  providedIn: 'root',
})
export class PolicyService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  issuePolicy(request: PolicyIssueRequest): Observable<PolicyRecord> {
    return this.http.post<PolicyRecord>(`${this.baseUrl}/experience/policies`, request);
  }
}

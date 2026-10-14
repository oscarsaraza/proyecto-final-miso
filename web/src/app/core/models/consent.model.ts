export interface ConsentRequest {
  document_number: string;
  channel?: string;
  otp_code: string;
  terms_accepted: boolean;
  purpose?: string;
  scope?: string;
  validity_days?: number;
}

export interface ConsentRecord {
  consent_id: string;
  document_number: string;
  channel: string;
  purpose: string;
  scope: string;
  validity_days: number;
  status: string;
  consent_hash: string;
  granted_at: string;
  expires_at: string;
}

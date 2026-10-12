/** Contrato de emisión del BFF (POST /api/v1/experience/policies) */
import { PlanTier, QuoteTier } from './quote.model';

export interface PolicyIssueRequest {
  quote_id: string;
  tier: PlanTier;
}

export interface PolicyRecord {
  policy_number: string;
  quote_id: string;
  insured_document: string;
  conditions: QuoteTier;
  status: 'ISSUED';
  issued_at: string;
  valid_until: string;
  pdf_s3_key?: string | null;
}

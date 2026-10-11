/** Contrato de cotización del BFF (POST /api/v1/experience/quotes) */
export type PlanTier = 'basic' | 'standard' | 'premium';

export interface QuoteRequest {
  document_type: string;
  document_number: string;
  birth_date: string;
  insured_amount: number;
  city?: string;
  occupation_risk?: number;
}

export interface PremiumFactor {
  code: string;
  label: string;
  multiplier: number;
  amount: number;
}

export interface Coverage {
  id: string;
  name: string;
  limit: number;
  deductible: number;
}

export interface QuoteTier {
  tier: PlanTier;
  monthly_premium: number;
  annual_premium: number;
  coverages: Coverage[];
  breakdown: PremiumFactor[];
}

export interface QuoteResponse {
  quote_id: string;
  document_number: string;
  status: 'active' | 'degraded';
  score_applied: number;
  tiers: QuoteTier[];
  created_at: string;
  expires_at: string;
}

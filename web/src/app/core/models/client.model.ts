/** Contratos de datos del cliente y del riesgo crediticio (HU-WEB-02) */

export interface ClientIdentification {
  document_type: string;
  document_number: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  email: string;
  phone: string;
}

export interface RiskData {
  financial_entity: string;
  insured_amount: number;
  term_months: number;
  occupation_risk: number;
  city: string;
}

export interface ClientValidationResponse {
  status: 'ELIGIBLE' | 'INELIGIBLE';
  age: number;
  message?: string;
}

export interface ClientQuoteSubmission {
  client: ClientIdentification;
  risk: RiskData;
}

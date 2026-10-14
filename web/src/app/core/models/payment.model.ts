/** Contrato de cobro del BFF (POST /api/v1/experience/payments/charge) */
export type PaymentMethod = 'PSE' | 'CARD';

export interface PaymentChargeRequest {
  policy_number: string;
  amount: number;
  payment_method: PaymentMethod;
  token_or_account: string;
}

export interface PaymentReceipt {
  transaction_id: string;
  idempotency_key: string;
  policy_number: string;
  amount: number;
  status: 'APPROVED';
  receipt_number: string;
  created_at: string;
}

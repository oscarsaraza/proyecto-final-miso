import { Component, computed, input } from '@angular/core';
import { PremiumFactor, QuoteTier } from '../../../core/models/quote.model';

const COP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
const MULTIPLIER = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

interface BreakdownRow {
  code: string;
  label: string;
  amount: string;
  detail: string;
  kind: 'base' | 'increase' | 'discount' | 'neutral';
  share: number;
}

/** HU-WEB-03 · Desglose explicativo de la prima por factor */
@Component({
  selector: 'app-premium-breakdown',
  standalone: true,
  template: `
    <section class="breakdown" aria-labelledby="breakdown-title">
      <h3 id="breakdown-title">Así se compone la prima mensual</h3>
      <ul class="rows">
        @for (row of rows(); track row.code) {
          <li class="row" [attr.data-kind]="row.kind" [attr.data-code]="row.code">
            <div class="row-text">
              <span class="label">{{ row.label }}</span>
              <span class="detail">{{ row.detail }}</span>
            </div>
            <span class="amount">{{ row.amount }}</span>
            <span class="bar" aria-hidden="true"><span [style.width.%]="row.share"></span></span>
          </li>
        }
      </ul>
      <div class="total">
        <span>Prima mensual</span>
        <strong data-testid="total">{{ total() }}</strong>
      </div>
    </section>
  `,
  styles: [`
    .breakdown { border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: #fff; }
    h3 { margin: 0 0 16px; font-size: 16px; color: #0f172a; }
    .rows { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
    .row { display: grid; grid-template-columns: 1fr auto; gap: 4px 12px; align-items: baseline; }
    .row-text { display: flex; flex-direction: column; }
    .label { color: #1e293b; font-weight: 500; }
    .detail { color: #64748b; font-size: 12px; }
    .amount { font-variant-numeric: tabular-nums; font-weight: 600; }
    .row[data-kind='increase'] .amount { color: #b45309; }
    .row[data-kind='discount'] .amount { color: #0d9488; }
    .bar { grid-column: 1 / -1; height: 4px; background: #f1f5f9; border-radius: 2px; overflow: hidden; }
    .bar span { display: block; height: 100%; background: #0b5474; }
    .row[data-kind='increase'] .bar span { background: #f59e0b; }
    .row[data-kind='discount'] .bar span { background: #0d9488; }
    .total { display: flex; justify-content: space-between; margin-top: 16px; padding-top: 12px; border-top: 1px solid #e2e8f0; }
    .total strong { font-size: 18px; color: #0b5474; font-variant-numeric: tabular-nums; }
  `],
})
export class PremiumBreakdownComponent {
  readonly tier = input.required<QuoteTier>();

  readonly total = computed(() => COP.format(this.tier().monthly_premium));

  readonly rows = computed<BreakdownRow[]>(() => {
    const breakdown = this.tier().breakdown;
    const largest = Math.max(...breakdown.map((factor) => Math.abs(factor.amount)), 1);
    return breakdown.map((factor) => ({
      code: factor.code,
      label: factor.label,
      amount: formatAmount(factor),
      detail: factor.code === 'base_rate' ? 'Según la suma asegurada' : `Multiplicador ×${MULTIPLIER.format(factor.multiplier)}`,
      kind: kindOf(factor),
      share: (Math.abs(factor.amount) / largest) * 100,
    }));
  });
}

function kindOf(factor: PremiumFactor): BreakdownRow['kind'] {
  if (factor.code === 'base_rate') return 'base';
  if (factor.amount > 0) return 'increase';
  if (factor.amount < 0) return 'discount';
  return 'neutral';
}

function formatAmount(factor: PremiumFactor): string {
  const value = COP.format(Math.abs(factor.amount));
  if (factor.code === 'base_rate' || factor.amount === 0) return value;
  return factor.amount > 0 ? `+ ${value}` : `− ${value}`;
}

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { QuoteTier } from '../../../core/models/quote.model';
import { PremiumBreakdownComponent } from './premium-breakdown.component';

const COP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });

const TIER: QuoteTier = {
  tier: 'standard',
  monthly_premium: 31_024,
  annual_premium: 372_288,
  coverages: [],
  breakdown: [
    { code: 'base_rate', label: 'Tarifa base actuarial', multiplier: 1, amount: 27_360 },
    { code: 'age', label: 'Ajuste por edad (45 años)', multiplier: 1.18, amount: 4_925 },
    { code: 'occupation', label: 'Ajuste por riesgo de ocupación (nivel 1)', multiplier: 1, amount: 0 },
    { code: 'payment_history', label: 'Ajuste por historial de pago', multiplier: 0.9, amount: -3_229 },
    { code: 'plan', label: 'Ajuste por plan standard', multiplier: 1.1, amount: 1_968 },
  ],
};

describe('PremiumBreakdownComponent (HU-WEB-03)', () => {
  let fixture: ComponentFixture<PremiumBreakdownComponent>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [PremiumBreakdownComponent] }).compileComponents();
    fixture = TestBed.createComponent(PremiumBreakdownComponent);
    fixture.componentRef.setInput('tier', TIER);
    fixture.detectChanges();
    element = fixture.nativeElement as HTMLElement;
  });

  const row = (code: string) => element.querySelector(`[data-code="${code}"]`) as HTMLElement;

  it('muestra una fila por cada factor de la prima', () => {
    const labels = Array.from(element.querySelectorAll('.row .label')).map((node) => node.textContent?.trim());

    expect(labels).toEqual(TIER.breakdown.map((factor) => factor.label));
  });

  it('muestra el aporte en pesos colombianos de la tarifa base', () => {
    expect(row('base_rate').querySelector('.amount')?.textContent?.trim()).toBe(COP.format(27_360));
  });

  it('marca los recargos con signo positivo', () => {
    const amount = row('age').querySelector('.amount')?.textContent?.trim();

    expect(amount).toBe(`+ ${COP.format(4_925)}`);
    expect(row('age').dataset['kind']).toBe('increase');
  });

  it('marca los descuentos con signo negativo', () => {
    const amount = row('payment_history').querySelector('.amount')?.textContent?.trim();

    expect(amount).toBe(`− ${COP.format(3_229)}`);
    expect(row('payment_history').dataset['kind']).toBe('discount');
  });

  it('muestra sin signo los factores que no cambian la prima', () => {
    expect(row('occupation').querySelector('.amount')?.textContent?.trim()).toBe(COP.format(0));
    expect(row('occupation').dataset['kind']).toBe('neutral');
  });

  it('explica el multiplicador de cada ajuste', () => {
    expect(row('age').querySelector('.detail')?.textContent).toContain('×1,18');
    expect(row('base_rate').querySelector('.detail')?.textContent).toContain('suma asegurada');
  });

  it('muestra la prima mensual total', () => {
    expect(element.querySelector('[data-testid="total"]')?.textContent?.trim()).toBe(COP.format(31_024));
  });

  it('dibuja la barra del factor de mayor aporte al 100 %', () => {
    const bar = row('base_rate').querySelector('.bar span') as HTMLElement;

    expect(bar.style.width).toBe('100%');
  });

  it('se actualiza al cambiar de plan', () => {
    fixture.componentRef.setInput('tier', { ...TIER, monthly_premium: 20_000 });
    fixture.detectChanges();

    expect(element.querySelector('[data-testid="total"]')?.textContent?.trim()).toBe(COP.format(20_000));
  });
});

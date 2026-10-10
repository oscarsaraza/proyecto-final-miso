import { ComponentFixture, TestBed } from '@angular/core/testing';
import { QuoteResponse, QuoteTier } from '../../core/models/quote.model';
import { CotizadorComponent } from './cotizador.component';

describe('CotizadorComponent (Placeholder Flujo Comercial)', () => {
  let component: CotizadorComponent;
  let fixture: ComponentFixture<CotizadorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CotizadorComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(CotizadorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse el componente del cotizador', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar el título del cotizador', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Cotizador de Seguros de Vida');
  });

  it('debe mostrar las etapas del proceso comercial', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const steps = compiled.querySelectorAll('.step');
    expect(steps.length).toBe(5);
  });

  describe('desglose de la prima (HU-WEB-03)', () => {
    const tier = (name: QuoteTier['tier'], premium: number): QuoteTier => ({
      tier: name,
      monthly_premium: premium,
      annual_premium: premium * 12,
      coverages: [],
      breakdown: [{ code: 'base_rate', label: 'Tarifa base actuarial', multiplier: 1, amount: premium }],
    });

    const quote: QuoteResponse = {
      quote_id: 'QUO-1',
      document_number: '1020304050',
      status: 'active',
      score_applied: 700,
      tiers: [tier('basic', 20_000), tier('standard', 27_000), tier('premium', 36_000)],
      created_at: '2026-10-09T00:00:00Z',
      expires_at: '2026-10-24T00:00:00Z',
    };

    const total = () => (fixture.nativeElement as HTMLElement).querySelector('[data-testid="total"]')?.textContent;

    it('no muestra el desglose sin cotización', () => {
      expect((fixture.nativeElement as HTMLElement).querySelector('app-premium-breakdown')).toBeNull();
    });

    it('muestra el desglose del plan estándar por defecto', () => {
      component.quote.set(quote);
      fixture.detectChanges();

      expect(total()).toContain('27.000');
    });

    it('cambia el desglose al elegir otro plan', () => {
      component.quote.set(quote);
      fixture.detectChanges();

      const tabs = (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>('.tier-tab');
      tabs[2].click();
      fixture.detectChanges();

      expect(total()).toContain('36.000');
      expect(tabs[2].getAttribute('aria-selected')).toBe('true');
    });
  });
});

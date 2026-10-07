import { ComponentFixture, TestBed } from '@angular/core/testing';
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
});

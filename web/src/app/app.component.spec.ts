import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { AppComponent } from './app.component';
import { AuthService } from './core/auth/auth.service';
import { UserSession } from './core/models/auth.model';

describe('AppComponent (HU-WEB-13)', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let currentSessionSignal = signal<UserSession | null>(null);
  let authServiceSpy: {
    currentSession: typeof currentSessionSignal;
    logout: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    currentSessionSignal = signal<UserSession | null>(null);
    authServiceSpy = {
      currentSession: currentSessionSignal,
      logout: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crear el componente principal', () => {
    expect(component).toBeTruthy();
  });

  it('debe tener el título corporativo de Solventa', () => {
    expect(component.title).toEqual('Solventa · Portal Asesores');
  });

  it('debe renderizar el logo de Solventa en el encabezado', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.logo-text')?.textContent).toContain('Solventa');
  });

  it('debe mostrar el badge Portal Asesores cuando no hay sesión activa', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.env-badge')?.textContent).toContain('Portal Asesores');
    expect(compiled.querySelector('.user-greeting')).toBeNull();
    expect(compiled.querySelector('.btn-logout')).toBeNull();
  });

  it('debe mostrar el nombre del asesor y botón de cierre de sesión cuando hay sesión activa', () => {
    currentSessionSignal.set({
      accessToken: 'token',
      refreshToken: 'refresh',
      tokenType: 'bearer',
      role: 'advisor',
      advisorName: 'Carlos Asesor',
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.env-badge')).toBeNull();
    expect(compiled.querySelector('.user-greeting')?.textContent).toContain('Carlos Asesor');
    expect(compiled.querySelector('.btn-logout')).toBeTruthy();
  });

  it('debe invocar authService.logout() al pulsar el botón de cierre de sesión', () => {
    currentSessionSignal.set({
      accessToken: 'token',
      refreshToken: 'refresh',
      tokenType: 'bearer',
      role: 'advisor',
      advisorName: 'Carlos Asesor',
    });
    fixture.detectChanges();

    const logoutBtn = fixture.nativeElement.querySelector('.btn-logout') as HTMLButtonElement;
    logoutBtn.click();

    expect(authServiceSpy.logout).toHaveBeenCalled();
  });
});

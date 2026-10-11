import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';
import { LoginComponent } from './login.component';
import { AuthService } from '../../core/auth/auth.service';
import { UserSession } from '../../core/models/auth.model';

describe('LoginComponent (HU-WEB-13)', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authServiceSpy: { login: ReturnType<typeof vi.fn> };
  let routerSpy: { navigateByUrl: ReturnType<typeof vi.fn> };
  let activatedRouteMock: { snapshot: { queryParams: Record<string, string> } };

  const mockSession: UserSession = {
    accessToken: 'mock-access-token',
    refreshToken: 'mock-refresh-token',
    tokenType: 'bearer',
    role: 'advisor',
    advisorName: 'Carlos Asesor',
    expiresIn: 900,
  };

  beforeEach(async () => {
    authServiceSpy = {
      login: vi.fn().mockReturnValue(of(mockSession)),
    };
    routerSpy = {
      navigateByUrl: vi.fn(),
    };
    activatedRouteMock = {
      snapshot: { queryParams: {} },
    };

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
        { provide: ActivatedRoute, useValue: activatedRouteMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse el componente de login', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar los campos para usuario, contraseña y código 2FA', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#username')).toBeTruthy();
    expect(compiled.querySelector('#password')).toBeTruthy();
    expect(compiled.querySelector('#totp')).toBeTruthy();
  });

  it('debe autenticar exitosamente y redirigir a /cotizador por defecto', () => {
    component.username = 'asesor@solventa.com';
    component.password = 'SuperSecreta2026*';
    component.totpCode = '123456';

    component.onSubmit();

    expect(authServiceSpy.login).toHaveBeenCalledWith({
      username: 'asesor@solventa.com',
      password: 'SuperSecreta2026*',
      totpCode: '123456',
    });
    expect(routerSpy.navigateByUrl).toHaveBeenCalledWith('/cotizador');
    expect(component.loading()).toBe(false);
    expect(component.errorMessage()).toBe('');
  });

  it('debe redirigir a returnUrl si está presente en los queryParams', () => {
    activatedRouteMock.snapshot.queryParams = { returnUrl: '/cotizador/auto-123' };

    component.username = 'asesor@solventa.com';
    component.password = 'SuperSecreta2026*';
    component.totpCode = '654321';

    component.onSubmit();

    expect(routerSpy.navigateByUrl).toHaveBeenCalledWith('/cotizador/auto-123');
  });

  it('debe mostrar mensaje unificado de credenciales inválidas ante error 401', () => {
    const error401 = new HttpErrorResponse({
      status: 401,
      statusText: 'Unauthorized',
      error: { detail: 'Credenciales o código de verificación inválidos' },
    });
    authServiceSpy.login.mockReturnValue(throwError(() => error401));

    component.username = 'asesor@solventa.com';
    component.password = 'WrongPassword';
    component.totpCode = '000000';

    component.onSubmit();
    fixture.detectChanges();

    expect(component.errorMessage()).toBe('Credenciales o código de verificación inválidos');
    expect(component.isLocked()).toBe(false);
    expect(component.loading()).toBe(false);

    const alertEl = fixture.nativeElement.querySelector('.alert-box');
    expect(alertEl?.textContent).toContain('Credenciales o código de verificación inválidos');
    expect(alertEl?.classList.contains('alert-danger')).toBe(true);
  });

  it('debe mostrar mensaje explicativo de bloqueo de cuenta ante error 423', () => {
    const error423 = new HttpErrorResponse({
      status: 423,
      statusText: 'Locked',
      error: {
        detail:
          'Cuenta bloqueada por seguridad tras múltiples intentos fallidos. Intente nuevamente en 15 minutos.',
      },
    });
    authServiceSpy.login.mockReturnValue(throwError(() => error423));

    component.username = 'asesor@solventa.com';
    component.password = 'WrongPassword';
    component.totpCode = '000000';

    component.onSubmit();
    fixture.detectChanges();

    expect(component.errorMessage()).toContain('Cuenta bloqueada por seguridad tras múltiples intentos fallidos');
    expect(component.isLocked()).toBe(true);
    expect(component.loading()).toBe(false);

    const alertEl = fixture.nativeElement.querySelector('.alert-box');
    expect(alertEl?.classList.contains('alert-locked')).toBe(true);
  });

  it('debe mostrar mensaje de error de conexión ante fallo de red o error 500', () => {
    const error500 = new HttpErrorResponse({
      status: 500,
      statusText: 'Internal Server Error',
    });
    authServiceSpy.login.mockReturnValue(throwError(() => error500));

    component.username = 'asesor@solventa.com';
    component.password = 'SuperSecreta2026*';
    component.totpCode = '123456';

    component.onSubmit();
    fixture.detectChanges();

    expect(component.errorMessage()).toContain('Error de comunicación con el servidor');
    expect(component.loading()).toBe(false);
  });

  it('no debe llamar al servicio si los campos obligatorios están incompletos', () => {
    component.username = '';
    component.password = '';
    component.totpCode = '';

    component.onSubmit();

    expect(authServiceSpy.login).not.toHaveBeenCalled();
    expect(component.errorMessage()).toBe('');
  });
});

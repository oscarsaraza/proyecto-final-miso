import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { LoginResponseDto, UserCredentials } from '../models/auth.model';

describe('AuthService (HU-WEB-13)', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let router: Router;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        AuthService,
      ],
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    httpMock.verify();
    sessionStorage.clear();
  });

  it('debe inicializarse sin sesión activa cuando sessionStorage está vacío', () => {
    expect(service.isAuthenticated()).toBe(false);
    expect(service.currentSession()).toBeNull();
  });

  it('debe autenticar al asesor comercial y guardar la sesión en memoria y sessionStorage', () => {
    const credentials: UserCredentials = {
      username: 'asesor@solventa.com',
      password: 'SuperSecreta2026*',
      totpCode: '123456',
    };

    const mockResponse: LoginResponseDto = {
      access_token: 'fake-access-token',
      refresh_token: 'fake-refresh-token',
      token_type: 'bearer',
      role: 'advisor',
      advisor_name: 'Carlos Asesor',
      expires_in: 900,
    };

    service.login(credentials).subscribe((session) => {
      expect(session.accessToken).toBe('fake-access-token');
      expect(session.refreshToken).toBe('fake-refresh-token');
      expect(session.role).toBe('advisor');
      expect(session.advisorName).toBe('Carlos Asesor');
    });

    const req = httpMock.expectOne('/api/v1/experience/auth/login');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      username: 'asesor@solventa.com',
      password: 'SuperSecreta2026*',
      totp_code: '123456',
    });
    req.flush(mockResponse);

    expect(service.isAuthenticated()).toBe(true);
    expect(service.currentSession()?.advisorName).toBe('Carlos Asesor');
    expect(sessionStorage.getItem('solventa_advisor_session')).toContain('fake-access-token');
  });

  it('debe renovar la sesión mediante refresh token silenciosamente', () => {
    // Simular sesión existente
    const initialResponse: LoginResponseDto = {
      access_token: 'expired-token',
      refresh_token: 'valid-refresh-token',
      token_type: 'bearer',
      role: 'advisor',
      advisor_name: 'Carlos Asesor',
      expires_in: 900,
    };

    service.login({ username: 'u', password: 'p', totpCode: '123456' }).subscribe();
    httpMock.expectOne('/api/v1/experience/auth/login').flush(initialResponse);

    const refreshedResponse: LoginResponseDto = {
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      token_type: 'bearer',
      role: 'advisor',
      advisor_name: 'Carlos Asesor',
      expires_in: 900,
    };

    service.refreshToken().subscribe((session) => {
      expect(session.accessToken).toBe('new-access-token');
    });

    const refreshReq = httpMock.expectOne('/api/v1/experience/auth/refresh');
    expect(refreshReq.request.method).toBe('POST');
    expect(refreshReq.request.body).toEqual({ refresh_token: 'valid-refresh-token' });
    refreshReq.flush(refreshedResponse);

    expect(service.currentSession()?.accessToken).toBe('new-access-token');
  });

  it('debe limpiar la sesión y redirigir a /login al ejecutar logout', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');

    // Cargar sesión
    service.login({ username: 'u', password: 'p', totpCode: '123456' }).subscribe();
    httpMock.expectOne('/api/v1/experience/auth/login').flush({
      access_token: 'tok',
      refresh_token: 'ref',
      token_type: 'bearer',
      role: 'advisor',
      advisor_name: 'Carlos Asesor',
      expires_in: 900,
    });

    expect(service.isAuthenticated()).toBe(true);

    service.logout();

    expect(service.isAuthenticated()).toBe(false);
    expect(service.currentSession()).toBeNull();
    expect(sessionStorage.getItem('solventa_advisor_session')).toBeNull();
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
  });
});

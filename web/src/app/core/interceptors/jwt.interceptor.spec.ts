import { TestBed } from '@angular/core/testing';
import { HttpClient, HttpErrorResponse, provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { jwtInterceptor } from './jwt.interceptor';
import { AuthService } from '../auth/auth.service';
import { UserSession } from '../models/auth.model';

describe('jwtInterceptor (HU-WEB-13.3)', () => {
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;
  let authServiceSpy: {
    currentSession: ReturnType<typeof vi.fn>;
    refreshToken: ReturnType<typeof vi.fn>;
    logout: ReturnType<typeof vi.fn>;
  };

  const mockSession: UserSession = {
    accessToken: 'initial-access-token',
    refreshToken: 'valid-refresh-token',
    tokenType: 'bearer',
    role: 'advisor',
    advisorName: 'Carlos Asesor',
    expiresIn: 900,
  };

  beforeEach(() => {
    authServiceSpy = {
      currentSession: vi.fn().mockReturnValue(mockSession),
      refreshToken: vi.fn(),
      logout: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([jwtInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authServiceSpy },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe agregar cabecera Authorization Bearer a peticiones autenticadas', () => {
    httpClient.get('/api/v1/experience/quotes/test').subscribe();

    const req = httpMock.expectOne('/api/v1/experience/quotes/test');
    expect(req.request.headers.has('Authorization')).toBe(true);
    expect(req.request.headers.get('Authorization')).toBe('Bearer initial-access-token');
    req.flush({ status: 'ok' });
  });

  it('no debe inyectar cabecera Authorization en endpoints públicos de autenticación', () => {
    httpClient.post('/api/v1/experience/auth/login', {}).subscribe();

    const req = httpMock.expectOne('/api/v1/experience/auth/login');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({ access_token: 'new' });
  });

  it('debe capturar error 401, renovar sesión silenciosamente y reintentar la petición original con nuevo token', () => {
    const refreshedSession: UserSession = {
      ...mockSession,
      accessToken: 'refreshed-access-token',
    };
    authServiceSpy.refreshToken.mockReturnValue(of(refreshedSession));

    httpClient.get('/api/v1/experience/quotes/secure').subscribe((response) => {
      expect(response).toEqual({ data: 'success' });
    });

    // Primera llamada rechazada con 401
    const req1 = httpMock.expectOne('/api/v1/experience/quotes/secure');
    expect(req1.request.headers.get('Authorization')).toBe('Bearer initial-access-token');
    req1.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    // Verificación de intento de renovación
    expect(authServiceSpy.refreshToken).toHaveBeenCalled();

    // Reintento automático con el nuevo token
    const req2 = httpMock.expectOne('/api/v1/experience/quotes/secure');
    expect(req2.request.headers.get('Authorization')).toBe('Bearer refreshed-access-token');
    req2.flush({ data: 'success' });
  });

  it('debe cerrar sesión (logout) si la renovación de sesión falla ante un error 401', () => {
    authServiceSpy.refreshToken.mockReturnValue(throwError(() => new Error('Refresh token expirado')));

    httpClient.get('/api/v1/experience/quotes/secure').subscribe({
      error: (err) => {
        expect(err).toBeDefined();
      },
    });

    const req = httpMock.expectOne('/api/v1/experience/quotes/secure');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(authServiceSpy.refreshToken).toHaveBeenCalled();
    expect(authServiceSpy.logout).toHaveBeenCalled();
  });
});

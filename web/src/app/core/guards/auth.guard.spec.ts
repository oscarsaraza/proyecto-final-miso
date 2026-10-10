import { TestBed } from '@angular/core/testing';
import { Router, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
import { of, throwError } from 'rxjs';
import { authGuard } from './auth.guard';
import { AuthService } from '../auth/auth.service';

describe('authGuard (HU-WEB-13)', () => {
  let authServiceSpy: {
    isAuthenticated: ReturnType<typeof vi.fn>;
    currentSession: ReturnType<typeof vi.fn>;
    refreshToken: ReturnType<typeof vi.fn>;
  };
  let router: Router;

  const mockRoute = {} as ActivatedRouteSnapshot;
  const mockState = { url: '/cotizador' } as RouterStateSnapshot;

  beforeEach(() => {
    authServiceSpy = {
      isAuthenticated: vi.fn(),
      currentSession: vi.fn(),
      refreshToken: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        {
          provide: Router,
          useValue: {
            createUrlTree: vi.fn((commands, extras) => ({ commands, extras }) as unknown as UrlTree),
          },
        },
      ],
    });

    router = TestBed.inject(Router);
  });

  it('debe permitir la navegación si el asesor ya está autenticado', () => {
    authServiceSpy.isAuthenticated.mockReturnValue(true);

    const result = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));
    expect(result).toBe(true);
  });

  it('debe redirigir al login preservando el returnUrl si no hay sesión ni refresh token', () => {
    authServiceSpy.isAuthenticated.mockReturnValue(false);
    authServiceSpy.currentSession.mockReturnValue(null);

    const result = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState)) as UrlTree;
    expect(result).toBeDefined();
    expect(router.createUrlTree).toHaveBeenCalledWith(['/login'], {
      queryParams: { returnUrl: '/cotizador' },
    });
  });

  it('debe intentar renovación silenciosa si existe refresh token previo a la navegación', async () => {
    authServiceSpy.isAuthenticated.mockReturnValue(false);
    authServiceSpy.currentSession.mockReturnValue({
      accessToken: '',
      refreshToken: 'valid-refresh-token',
    });
    authServiceSpy.refreshToken.mockReturnValue(of({ accessToken: 'new-token' }));

    const result$ = TestBed.runInInjectionContext(() => authGuard(mockRoute, mockState));

    if (typeof result$ === 'object' && 'subscribe' in result$) {
      result$.subscribe((allowed) => {
        expect(allowed).toBe(true);
      });
    }
  });
});


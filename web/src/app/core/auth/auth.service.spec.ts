import { TestBed } from '@angular/core/testing';
import { AuthService } from './auth.service';

describe('AuthService (Scaffolding y Placeholders)', () => {
  let service: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthService);
  });

  it('debe crearse correctamente el servicio de autenticación', () => {
    expect(service).toBeTruthy();
  });

  it('debe iniciar sin sesión autenticada', () => {
    expect(service.isAuthenticated()).toBe(false);
    expect(service.currentSession()).toBeNull();
  });

  it('debe lanzar error informativo al invocar login antes de implementar HU-WEB-13', () => {
    expect(() => {
      service.login({
        username: 'asesor@solventa.com',
        password: 'password123',
        totpCode: '123456',
      });
    }).toThrow(/HU-WEB-13/);
  });
});

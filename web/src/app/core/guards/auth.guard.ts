import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { AuthService } from '../auth/auth.service';

/**
 * Guardia de navegación para proteger rutas exclusivas de asesores autenticados (HU-WEB-13).
 * Redirige al login preservando el returnUrl si la sesión no es válida o expira.
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  const session = authService.currentSession();
  if (session?.refreshToken) {
    // Intentar renovación silenciosa previa a la navegación (Criterio 3)
    return authService.refreshToken().pipe(
      map(() => true),
      catchError(() => {
        return of(
          router.createUrlTree(['/login'], {
            queryParams: { returnUrl: state.url },
          }),
        );
      }),
    );
  }

  // Redirigir al login conservando la URL de destino
  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url },
  });
};


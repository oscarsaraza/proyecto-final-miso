import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../auth/auth.service';

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const session = authService.currentSession();

  if (session?.accessToken) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${session.accessToken}`
      }
    });
  }

  return next(req);
};

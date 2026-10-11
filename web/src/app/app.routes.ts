import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login.component';
import { CotizadorComponent } from './features/cotizador/cotizador.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'cotizador', component: CotizadorComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'login' },
];


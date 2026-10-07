import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login.component';
import { CotizadorComponent } from './features/cotizador/cotizador.component';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'cotizador', component: CotizadorComponent },
  { path: '**', redirectTo: 'login' },
];

import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'Solventa · Portal Asesores';
  private readonly authService = inject(AuthService);
  readonly currentSession = this.authService.currentSession;

  logout(): void {
    this.authService.logout();
  }
}

export { AppComponent as App };

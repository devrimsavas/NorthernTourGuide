import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { ThemeService } from '../../services/theme.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './header.component.html',
  host: {class:'sticky top-0 z-50 block'},
})
export class HeaderComponent {
  protected readonly theme = inject(ThemeService);
  protected readonly auth=inject(AuthService)
  protected readonly menuOpen = signal(false);

  protected readonly links = [
    { path: '/', label: 'Home', exact: true },
    { path: '/tours', label: 'Tours', exact: false },
    { path: '/guides', label: 'Guides', exact: false },
  ];

  toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  closeMenu(): void {
    this.menuOpen.set(false);
  }
  logout():void {
    this.closeMenu();
    this.auth.logout();
  }
}
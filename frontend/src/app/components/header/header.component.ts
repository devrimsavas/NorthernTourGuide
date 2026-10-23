import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { filter, map } from 'rxjs';
import { ThemeService } from '../../services/theme.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './header.component.html',
  host: {
    class: 'sticky top-0 z-50 block',
    '(window:scroll)': 'onScroll()',
  },
})
export class HeaderComponent {
  protected readonly theme = inject(ThemeService);
  protected readonly auth = inject(AuthService);
  protected readonly menuOpen = signal(false);
  private readonly router = inject(Router);

  private readonly scrolled = signal(false);

  private readonly isHome = toSignal(
    this.router.events.pipe(
      filter((event) => event instanceof NavigationEnd),
      map((event) => event.urlAfterRedirects.split('?')[0] === '/'),
    ),
    { initialValue: this.router.url.split('?')[0] === '/' },
  );

  protected readonly transparent = computed(
    () => this.isHome() && !this.scrolled() && !this.menuOpen(),
  );

  protected readonly headerClasses = computed(() =>
    this.transparent()
      ? 'dark border-b border-transparent bg-transparent transition-colors duration-300'
      : 'border-b border-slate-200 bg-white/80 backdrop-blur transition-colors duration-300 dark:border-slate-800 dark:bg-slate-950/80',
  );

  onScroll(): void {
    this.scrolled.set(window.scrollY > 10);
  }

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
  logout(): void {
    this.closeMenu();
    this.auth.logout();
  }
}

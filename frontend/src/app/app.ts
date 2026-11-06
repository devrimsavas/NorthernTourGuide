import { Component, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { HeaderComponent } from './components/header/header.component';
import { FooterComponent } from './components/footer/footer.component';

declare global {
  interface Window {
    goatcounter?: { count: (vars?: { path?: string }) => void };
  }
}

@Component({
  imports: [RouterOutlet, HeaderComponent, FooterComponent],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('frontend');

  private readonly router = inject(Router);

  constructor() {
    // Count every page the visitor opens inside the app
    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event) => this.countPage(event.urlAfterRedirects));
  }

  private countPage(path: string): void {
    if (window.goatcounter) {
      window.goatcounter.count({ path });
      return;
    }

    // The script loads asynchronously: on the very first page, wait until it is ready
    const script = document.querySelector<HTMLScriptElement>('script[data-goatcounter]');
    script?.addEventListener('load', () => window.goatcounter?.count({ path }), { once: true });
  }
}

import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { catchError, map, of, startWith } from 'rxjs';

import { Guide } from '../models/guide.model';
import { GuideService } from '../services/guide.service';

type GuidesState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'loaded'; guides: Guide[] };

@Component({
  selector: 'app-guides',
  templateUrl: '../pages/guides.component.html',
  imports: [RouterLink],
})
export class GuidesComponent {
  private readonly guideService = inject(GuideService);

  protected readonly state = toSignal(
    this.guideService.getGuides().pipe(
      map((guides): GuidesState => ({ status: 'loaded', guides })),
      catchError(() => of<GuidesState>({ status: 'error' })),
      startWith<GuidesState>({ status: 'loading' }),
    ),
    { initialValue: { status: 'loading' } as GuidesState },
  );

  protected languages(guide: Guide): string[] {
    return guide.languages
      .split(',')
      .map((language) => language.trim())
      .filter(Boolean);
  }
}
import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, ParamMap, Router, RouterLink } from '@angular/router';
import { catchError, map, of, startWith, switchMap } from 'rxjs';

import { ActivityType, TourLocation } from '../models/lookup.model';
import { Paginated } from '../models/paginated.model';
import { Difficulty, Tour } from '../models/tour.model';
import { LookupService } from '../services/lookup.service';
import { TourFilters, TourService } from '../services/tour.service';
import { TourCardComponent } from './tour-card/tour-card.component';

const PAGE_SIZE = 9;

type ToursState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'loaded'; page: Paginated<Tour> };

function toNumber(value: string | null): number | undefined {
  return value ? Number(value) : undefined;
}

function toTourFilters(params: ParamMap): TourFilters {
  return {
    location: toNumber(params.get('location')),
    activity_type: toNumber(params.get('activity_type')),
    difficulty: (params.get('difficulty') as Difficulty) || undefined,
    max_price: toNumber(params.get('max_price')),
    date_from: params.get('date_from') || undefined,
    date_to: params.get('date_to') || undefined,
    page: toNumber(params.get('page')) ?? 1,
    page_size: PAGE_SIZE,
  };
}

@Component({
  selector: 'app-tours',
  templateUrl: '../pages/tours.component.html',
  imports: [RouterLink, TourCardComponent],
})
export class ToursComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly tourService = inject(TourService);
  private readonly lookupService = inject(LookupService);

  protected readonly difficulties: Difficulty[] = ['easy', 'moderate', 'challenging'];

  protected readonly locations = toSignal(
    this.lookupService.getLocations().pipe(catchError(() => of([] as TourLocation[]))),
    { initialValue: [] as TourLocation[] },
  );

  protected readonly activityTypes = toSignal(
    this.lookupService.getActivityTypes().pipe(catchError(() => of([] as ActivityType[]))),
    { initialValue: [] as ActivityType[] },
  );

  protected readonly filters = toSignal(this.route.queryParamMap.pipe(map(toTourFilters)), {
    requireSync: true,
  });

  protected readonly state = toSignal(
    this.route.queryParamMap.pipe(
      switchMap((params) =>
        this.tourService.getTours(toTourFilters(params)).pipe(
          map((page): ToursState => ({ status: 'loaded', page })),
          catchError(() => of<ToursState>({ status: 'error' })),
          startWith<ToursState>({ status: 'loading' }),
        ),
      ),
    ),
    { initialValue: { status: 'loading' } as ToursState },
  );

  protected readonly totalPages = computed(() => {
    const state = this.state();
    return state.status === 'loaded' ? Math.ceil(state.page.count / PAGE_SIZE) : 0;
  });

  protected readonly hasActiveFilters = computed(() => {
    const { location, activity_type, difficulty, max_price, date_from, date_to } = this.filters();
    return [location, activity_type, difficulty, max_price, date_from, date_to].some(
      (value) => value !== undefined,
    );
  });

  onFilterChange(key: keyof TourFilters, event: Event): void {
    const value = (event.target as HTMLInputElement | HTMLSelectElement).value;
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { [key]: value || null, page: null },
      queryParamsHandling: 'merge',
    });
  }

  goToPage(page: number): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { page: page > 1 ? page : null },
      queryParamsHandling: 'merge',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  clearFilters(): void {
    this.router.navigate([], { relativeTo: this.route, queryParams: {} });
  }
}
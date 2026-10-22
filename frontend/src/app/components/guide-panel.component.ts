import { CurrencyPipe, DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { BehaviorSubject, catchError, combineLatest, map, of, startWith, switchMap } from 'rxjs';

import { GuideBooking, GuideTour } from '../models/guide-panel.model';
import { ActivityType, TourLocation } from '../models/lookup.model';
import { TourSlot } from '../models/tour.model';
import { GuidePanelService } from '../services/guide-panel.service';
import { LookupService } from '../services/lookup.service';

type LoadState<T> = { status: 'loading' } | { status: 'error' } | { status: 'loaded'; data: T };

interface SlotGroup {
  slotId: number;
  tour: string;
  startTime: string;
  bookings: GuideBooking[];
  participants: number;
}

function load<T>(source: BehaviorSubject<void>, request: () => import('rxjs').Observable<T>) {
  return source.pipe(
    switchMap((_, reloadCount) => {
      const request$ = request().pipe(
        map((data): LoadState<T> => ({ status: 'loaded', data })),
        catchError(() => of<LoadState<T>>({ status: 'error' })),
      );
      return reloadCount === 0 ? request$.pipe(startWith<LoadState<T>>({ status: 'loading' })) : request$;
    }),
  );
}

@Component({
  selector: 'app-guide-panel',
  templateUrl: '../pages/guide-panel.component.html',
  imports: [RouterLink, CurrencyPipe, DatePipe],
})
export class GuidePanelComponent {
  private readonly panelService = inject(GuidePanelService);
  private readonly lookupService = inject(LookupService);

  private readonly bookingsReload$ = new BehaviorSubject<void>(undefined);
  private readonly toursReload$ = new BehaviorSubject<void>(undefined);
  private readonly slotsReload$ = new BehaviorSubject<void>(undefined);

  // Bookings
  protected readonly bookings = toSignal(
    load(this.bookingsReload$, () => this.panelService.getBookings()),
    { initialValue: { status: 'loading' } as LoadState<GuideBooking[]> },
  );

  protected readonly upcomingGroups = computed<SlotGroup[]>(() => {
    const state = this.bookings();
    if (state.status !== 'loaded') return [];

    const groups = new Map<number, SlotGroup>();
    for (const booking of state.data) {
      if (Date.parse(booking.start_time) <= Date.now()) continue;

      const group = groups.get(booking.slot) ?? {
        slotId: booking.slot,
        tour: booking.tour,
        startTime: booking.start_time,
        bookings: [],
        participants: 0,
      };
      group.bookings.push(booking);
      if (booking.status !== 'cancelled') {
        group.participants += booking.participants;
      }
      groups.set(booking.slot, group);
    }
    return [...groups.values()].sort((a, b) => Date.parse(a.startTime) - Date.parse(b.startTime));
  });

  // Tours
  protected readonly tours = toSignal(
    load(this.toursReload$, () => this.panelService.getTours()),
    { initialValue: { status: 'loading' } as LoadState<GuideTour[]> },
  );

  private readonly locations = toSignal(
    this.lookupService.getLocations().pipe(catchError(() => of([] as TourLocation[]))),
    { initialValue: [] as TourLocation[] },
  );

  private readonly activityTypes = toSignal(
    this.lookupService.getActivityTypes().pipe(catchError(() => of([] as ActivityType[]))),
    { initialValue: [] as ActivityType[] },
  );

  protected readonly locationNames = computed(
    () => new Map(this.locations().map((location) => [location.id, location.name])),
  );

  protected readonly activityNames = computed(
    () => new Map(this.activityTypes().map((activity) => [activity.id, activity.name])),
  );

  // Slots of the expanded tour
  protected readonly expandedTourId = signal<number | null>(null);

  protected readonly slots = toSignal(
    combineLatest([toObservable(this.expandedTourId), this.slotsReload$]).pipe(
      switchMap(([tourId]) =>
        tourId === null
          ? of(null)
          : this.panelService.getSlots(tourId).pipe(
              map((data): LoadState<TourSlot[]> => ({ status: 'loaded', data })),
              catchError(() => of<LoadState<TourSlot[]>>({ status: 'error' })),
            ),
      ),
    ),
    { initialValue: null },
  );

  protected readonly newSlotTime = signal('');
  protected readonly busy = signal(false);
  protected readonly actionError = signal<string | null>(null);

  toggleExpanded(tour: GuideTour): void {
    this.expandedTourId.update((current) => (current === tour.id ? null : tour.id));
    this.newSlotTime.set('');
    this.actionError.set(null);
  }

  onSlotTimeInput(event: Event): void {
    this.newSlotTime.set((event.target as HTMLInputElement).value);
  }

  toggleActive(tour: GuideTour): void {
    this.busy.set(true);
    this.actionError.set(null);
    this.panelService.updateTour(tour.id, { is_active: !tour.is_active }).subscribe({
      next: () => {
        this.busy.set(false);
        this.toursReload$.next();
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.actionError.set(this.errorMessage(error, 'The tour could not be updated.'));
      },
    });
  }

  addSlot(tour: GuideTour): void {
    const startTime = this.newSlotTime();
    if (!startTime) return;

    this.busy.set(true);
    this.actionError.set(null);
    this.panelService.addSlot(tour.id, startTime).subscribe({
      next: () => {
        this.busy.set(false);
        this.newSlotTime.set('');
        this.slotsReload$.next();
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.actionError.set(this.errorMessage(error, 'The date could not be added.'));
      },
    });
  }

  private errorMessage(error: HttpErrorResponse, fallback: string): string {
    const body = error.error ?? {};
    const detail = body.start_time ?? body.max_participants ?? body.detail;
    if (detail) {
      return Array.isArray(detail) ? detail[0] : String(detail);
    }
    return fallback;
  }
}
import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { BehaviorSubject, catchError, map, of, startWith, switchMap } from 'rxjs';

import { CreatedBooking } from '../models/booking.model';
import { AuroraChance, SlotForecast } from '../models/forecast.model';
import { TourDetail, TourSlot } from '../models/tour.model';
import { AuthService } from '../services/auth.service';
import { BookingService } from '../services/booking.service';
import { TourService } from '../services/tour.service';

type TourState =
  | { status: 'loading' }
  | { status: 'not-found' }
  | { status: 'error' }
  | { status: 'loaded'; tour: TourDetail };

type BookingState =
  | { status: 'idle' }
  | { status: 'submitting' }
  | { status: 'success'; booking: CreatedBooking }
  | { status: 'error'; message: string };

@Component({
  selector: 'app-tour-detail',
  templateUrl: '../pages/tour-detail.component.html',
  imports: [RouterLink, CurrencyPipe, DatePipe, DecimalPipe],
})
export class TourDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly tourService = inject(TourService);
  private readonly bookingService = inject(BookingService);
  protected readonly auth = inject(AuthService);

  private readonly tourId$ = this.route.paramMap.pipe(map((params) => Number(params.get('id'))));
  private readonly reload$ = new BehaviorSubject<void>(undefined);

  protected readonly state = toSignal(
    this.tourId$.pipe(
      switchMap((id) =>
        this.reload$.pipe(
          switchMap((_, reloadCount) => {
            const request$ = this.tourService.getTour(id).pipe(
              map((tour): TourState => ({ status: 'loaded', tour })),
              catchError((error: HttpErrorResponse) =>
                of<TourState>({ status: error.status === 404 ? 'not-found' : 'error' }),
              ),
            );
            return reloadCount === 0
              ? request$.pipe(startWith<TourState>({ status: 'loading' }))
              : request$;
          }),
        ),
      ),
    ),
    { initialValue: { status: 'loading' } as TourState },
  );

  protected readonly forecast = toSignal(
    this.tourId$.pipe(
      switchMap((id) => this.tourService.getForecast(id).pipe(catchError(() => of(null)))),
    ),
    { initialValue: null },
  );

  protected readonly reviews = toSignal(
    this.tourId$.pipe(
      switchMap((id) => this.tourService.getReviews(id).pipe(catchError(() => of(null)))),
    ),
    { initialValue: null },
  );

  protected readonly forecastBySlot = computed(
    () =>
      new Map<number, SlotForecast>(
        (this.forecast()?.slots ?? []).map((slot) => [slot.slot_id, slot]),
      ),
  );

  protected readonly selectedImage = signal(0);
  private readonly fragment = toSignal(this.route.fragment, { initialValue: null });
  private hasScrolledToDates = false;

  constructor() {
    effect(() => {
      if (
        this.hasScrolledToDates ||
        this.fragment() !== 'dates' ||
        this.state().status !== 'loaded'
      ) {
        return;
      }
      this.hasScrolledToDates = true;
      setTimeout(() => document.getElementById('dates')?.scrollIntoView({ behavior: 'smooth' }));
    });
    effect(() => {
      const slot = this.selectedSlot();
      if (!slot) return;
      if (slot.available_spots === 0) {
        this.selectedSlotId.set(null);
      } else if (this.participants() > slot.available_spots) {
        this.participants.set(slot.available_spots);
      }
    });
  }

  // Booking
  protected readonly selectedSlotId = signal<number | null>(null);
  protected readonly participants = signal(1);
  protected readonly booking = signal<BookingState>({ status: 'idle' });

  protected readonly selectedSlot = computed<TourSlot | null>(() => {
    const state = this.state();
    const slotId = this.selectedSlotId();
    if (state.status !== 'loaded' || slotId === null) return null;
    return state.tour.slots.find((slot) => slot.id === slotId) ?? null;
  });

  protected readonly totalPrice = computed(() => {
    const state = this.state();
    return state.status === 'loaded' ? Number(state.tour.price) * this.participants() : 0;
  });

  selectSlot(slot: TourSlot): void {
    if (slot.available_spots === 0) return;
    this.selectedSlotId.set(slot.id);
    this.participants.set(1);
    this.booking.set({ status: 'idle' });
  }

  changeParticipants(delta: number): void {
    const max = this.selectedSlot()?.available_spots ?? 1;
    this.participants.update((count) => Math.min(max, Math.max(1, count + delta)));
  }

  book(): void {
    const user = this.auth.currentUser();
    if (!user) {
      this.router.navigate(['/login'], { queryParams: { returnUrl: this.router.url } });
      return;
    }
    if (user.role !== 'customer') {
      this.booking.set({ status: 'error', message: 'Only customers can book tours.' });
      return;
    }

    const slotId = this.selectedSlotId();
    if (slotId === null) return;

    this.booking.set({ status: 'submitting' });
    this.bookingService.createBooking(slotId, this.participants()).subscribe({
      next: (created) => {
        this.booking.set({ status: 'success', booking: created });
        this.selectedSlotId.set(null);
        this.reload$.next();
      },
      error: (error: HttpErrorResponse) => {
        this.booking.set({ status: 'error', message: this.bookingErrorMessage(error) });
        if (error.status === 400) {
          this.reload$.next();
        }
      },
    });
  }

  protected weatherIcon(symbolCode: string | null): string {
    if (!symbolCode) return '';
    if (symbolCode.includes('thunder')) return '⛈️';
    if (symbolCode.includes('snow') || symbolCode.includes('sleet')) return '❄️';
    if (symbolCode.includes('rain')) return '🌧️';
    if (symbolCode.includes('fog')) return '🌫️';
    if (symbolCode.startsWith('cloudy')) return '☁️';
    if (symbolCode.startsWith('partlycloudy') || symbolCode.startsWith('fair')) return '⛅';
    if (symbolCode.startsWith('clearsky')) return symbolCode.endsWith('night') ? '🌙' : '☀️';
    return '🌡️';
  }

  protected auroraBadgeClass(chance: AuroraChance | null): string {
    switch (chance) {
      case 'high':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300';
      case 'medium':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    }
  }

  private bookingErrorMessage(error: HttpErrorResponse): string {
    const body = error.error ?? {};
    const detail = body.participants ?? body.slot ?? body.detail ?? body.non_field_errors;
    if (detail) {
      return Array.isArray(detail) ? detail[0] : String(detail);
    }
    return 'Booking failed. Please try again.';
  }
}

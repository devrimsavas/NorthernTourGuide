import { CurrencyPipe, DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { BehaviorSubject, catchError, map, of, startWith, switchMap } from 'rxjs';

import { MyBooking } from '../models/booking.model';
import { BookingService } from '../services/booking.service';

type ListState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'loaded'; bookings: MyBooking[] };

@Component({
  selector: 'app-my-bookings',
  templateUrl: '../pages/my-bookings.component.html',
  imports: [RouterLink, CurrencyPipe, DatePipe],
})
export class MyBookingsComponent {
  private readonly bookingService = inject(BookingService);
  private readonly reload$ = new BehaviorSubject<void>(undefined);

  protected readonly state = toSignal(
    this.reload$.pipe(
      switchMap((_, reloadCount) => {
        const request$ = this.bookingService.getMyBookings().pipe(
          map((bookings): ListState => ({ status: 'loaded', bookings })),
          catchError(() => of<ListState>({ status: 'error' })),
        );
        return reloadCount === 0 ? request$.pipe(startWith<ListState>({ status: 'loading' })) : request$;
      }),
    ),
    { initialValue: { status: 'loading' } as ListState },
  );

  protected readonly upcoming = computed(() =>
    this.bookingsWhere((start) => start > Date.now()).sort(
      (a, b) => Date.parse(a.start_time) - Date.parse(b.start_time),
    ),
  );

  protected readonly past = computed(() =>
    this.bookingsWhere((start) => start <= Date.now()).sort(
      (a, b) => Date.parse(b.start_time) - Date.parse(a.start_time),
    ),
  );

  protected readonly busyReference = signal<string | null>(null);
  protected readonly actionError = signal<string | null>(null);

  protected readonly reviewingReference = signal<string | null>(null);
  protected readonly rating = signal(5);
  protected readonly comment = signal('');

  cancel(booking: MyBooking): void {
    if (!confirm(`Cancel your booking for "${booking.tour}"?`)) return;

    this.busyReference.set(booking.reference);
    this.actionError.set(null);
    this.bookingService.cancelBooking(booking.reference).subscribe({
      next: () => {
        this.busyReference.set(null);
        this.reload$.next();
      },
      error: (error: HttpErrorResponse) => {
        this.busyReference.set(null);
        this.actionError.set(this.errorMessage(error, 'The booking could not be cancelled.'));
      },
    });
  }

  openReview(booking: MyBooking): void {
    this.reviewingReference.set(booking.reference);
    this.rating.set(5);
    this.comment.set('');
    this.actionError.set(null);
  }

  closeReview(): void {
    this.reviewingReference.set(null);
  }

  onCommentInput(event: Event): void {
    this.comment.set((event.target as HTMLTextAreaElement).value);
  }

  submitReview(booking: MyBooking): void {
    this.busyReference.set(booking.reference);
    this.actionError.set(null);
    this.bookingService
      .reviewBooking(booking.reference, { rating: this.rating(), comment: this.comment().trim() })
      .subscribe({
        next: () => {
          this.busyReference.set(null);
          this.reviewingReference.set(null);
          this.reload$.next();
        },
        error: (error: HttpErrorResponse) => {
          this.busyReference.set(null);
          this.actionError.set(this.errorMessage(error, 'The review could not be saved.'));
        },
      });
  }

  private bookingsWhere(predicate: (startTime: number) => boolean): MyBooking[] {
    const state = this.state();
    if (state.status !== 'loaded') return [];
    return state.bookings.filter((booking) => predicate(Date.parse(booking.start_time)));
  }

  private errorMessage(error: HttpErrorResponse, fallback: string): string {
    const body = error.error ?? {};
    const detail = body.status ?? body.booking ?? body.rating ?? body.detail;
    if (detail) {
      return Array.isArray(detail) ? detail[0] : String(detail);
    }
    return fallback;
  }
}
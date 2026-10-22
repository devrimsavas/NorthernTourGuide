import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { CreatedBooking, MyBooking, ReviewRequest } from '../models/booking.model';

@Injectable({ providedIn: 'root' })
export class BookingService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/bookings/`;

  createBooking(slotId: number, participants: number): Observable<CreatedBooking> {
    return this.http.post<CreatedBooking>(this.baseUrl, { slot: slotId, participants });
  }
  
  getMyBookings(): Observable<MyBooking[]> {
    return this.http.get<MyBooking[]>(`${this.baseUrl}me/`);
  }

  cancelBooking(reference: string): Observable<MyBooking> {
    return this.http.post<MyBooking>(`${this.baseUrl}${reference}/cancel/`, {});
  }

  reviewBooking(reference: string, review: ReviewRequest): Observable<unknown> {
    return this.http.post(`${this.baseUrl}${reference}/review/`, review);
  }
}

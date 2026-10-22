import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { GuideBooking, GuideTour, GuideTourInput } from '../models/guide-panel.model';
import { TourSlot } from '../models/tour.model';

@Injectable({ providedIn: 'root' })
export class GuidePanelService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/guide`;

  getTours(): Observable<GuideTour[]> {
    return this.http.get<GuideTour[]>(`${this.baseUrl}/tours/`);
  }

  createTour(tour: GuideTourInput): Observable<GuideTour> {
    return this.http.post<GuideTour>(`${this.baseUrl}/tours/`, tour);
  }

  updateTour(id: number, changes: Partial<GuideTourInput>): Observable<GuideTour> {
    return this.http.patch<GuideTour>(`${this.baseUrl}/tours/${id}/`, changes);
  }

  getSlots(tourId: number): Observable<TourSlot[]> {
    return this.http.get<TourSlot[]>(`${this.baseUrl}/tours/${tourId}/slots/`);
  }

  addSlot(tourId: number, startTime: string): Observable<TourSlot> {
    return this.http.post<TourSlot>(`${this.baseUrl}/tours/${tourId}/slots/`, { start_time: startTime });
  }

  getBookings(slotId?: number): Observable<GuideBooking[]> {
    const params = slotId ? new HttpParams().set('slot', slotId) : undefined;
    return this.http.get<GuideBooking[]>(`${this.baseUrl}/bookings/`, { params });
  }
}
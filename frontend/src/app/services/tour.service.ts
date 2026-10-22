import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Paginated } from '../models/paginated.model';
import { Difficulty, Tour, TourDetail } from '../models/tour.model';
import { TourForecast } from '../models/forecast.model';
import { Review } from '../models/review.model';

export interface TourFilters {
  location?: number;
  activity_type?: number;
  difficulty?: Difficulty;
  max_price?: number;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

@Injectable({ providedIn: 'root' })
export class TourService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/tours/`;

  getTours(filters: TourFilters = {}): Observable<Paginated<Tour>> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    }
    return this.http.get<Paginated<Tour>>(this.baseUrl, { params });
  }
  
  getTour(id: number): Observable<TourDetail> {
    return this.http.get<TourDetail>(`${this.baseUrl}${id}/`);
  }

  getForecast(id: number): Observable<TourForecast> {
    return this.http.get<TourForecast>(`${this.baseUrl}${id}/forecast/`);
  }

  getReviews(id: number, page = 1): Observable<Paginated<Review>> {
    const params = new HttpParams().set('page', page);
    return this.http.get<Paginated<Review>>(`${this.baseUrl}${id}/reviews/`, { params });
  }
}

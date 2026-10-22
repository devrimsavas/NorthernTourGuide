import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ActivityType, TourLocation } from '../models/lookup.model';

@Injectable({ providedIn: 'root' })
export class LookupService {
  private readonly http = inject(HttpClient);

  getLocations(): Observable<TourLocation[]> {
    return this.http.get<TourLocation[]>(`${environment.apiUrl}/locations/`);
  }

  getActivityTypes(): Observable<ActivityType[]> {
    return this.http.get<ActivityType[]>(`${environment.apiUrl}/activity-types/`);
  }
}

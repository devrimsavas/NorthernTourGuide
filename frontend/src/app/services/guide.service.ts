import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Guide } from '../models/guide.model';

@Injectable({ providedIn: 'root' })
export class GuideService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/guides/`;

  getGuides(): Observable<Guide[]> {
    return this.http.get<Guide[]>(this.baseUrl);
  }
}
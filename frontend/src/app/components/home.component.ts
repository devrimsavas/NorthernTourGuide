import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { Guide } from '../models/guide.model';
import { Tour } from '../models/tour.model';
import { GuideService } from '../services/guide.service';
import { TourService } from '../services/tour.service';
import { TourCardComponent } from './tour-card/tour-card.component';

interface Activity {
  name: string;
  description: string;
  image: string;
  activityTypeId: number;
}

interface Feature {
  title: string;
  text: string;
}

@Component({
  selector: 'app-home',
  templateUrl: '../pages/home.component.html',
  imports: [RouterLink,TourCardComponent],
})
export class HomeComponent {
  private readonly tourService = inject(TourService);
  private readonly guideService = inject(GuideService);

  protected readonly featuredTours = toSignal(
    this.tourService.getTours({ page_size: 3 }).pipe(
      map((page) => page.results),
      catchError(() => of([] as Tour[])),
    ),
    { initialValue: [] as Tour[] },
  );

  protected readonly guides = toSignal(
    this.guideService.getGuides().pipe(catchError(() => of([] as Guide[]))),
    { initialValue: [] as Guide[] },
  );

  protected readonly activities: Activity[] = [
    {
      name: 'Northern Lights',
      description: 'Chase the aurora far from the city lights.',
      image: '/images/northlighttour1.jpg',
      activityTypeId: 2,
    },
    {
      name: 'Husky Safari',
      description: 'Drive your own sled across the snowy plateau.',
      image: '/images/huskytour1.jpg',
      activityTypeId: 1,
    },
    {
      name: 'Sami Culture',
      description: 'Meet Sami hosts in a traditional lavvu.',
      image: '/images/samitour1.jpg',
      activityTypeId: 4,
    },
    {
      name: 'Snowshoe Hiking',
      description: 'Explore quiet forests at an easy pace.',
      image: '/images/snowshoes.jpg',
      activityTypeId: 3,
    },
  ];

  protected readonly features: Feature[] = [
    {
      title: 'Local guides',
      text: 'Small local operators who know every fjord, forest and husky by name.',
    },
    {
      title: 'Live aurora forecasts',
      text: 'Weather from MET Norway and Kp index from NOAA for every tour date.',
    },
    {
      title: 'Small groups, easy booking',
      text: 'Real-time availability, instant confirmation and free cancellation before the tour starts.',
    },
  ];
}
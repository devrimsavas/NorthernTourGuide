import { CurrencyPipe, DecimalPipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Tour } from '../../models/tour.model';

@Component({
  selector: 'app-tour-card',
  imports: [RouterLink, CurrencyPipe, DecimalPipe],
  templateUrl: './tour-card.component.html',
})
export class TourCardComponent {
  readonly tour = input.required<Tour>();
}
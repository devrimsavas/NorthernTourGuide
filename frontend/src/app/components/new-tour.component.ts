import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { catchError, of } from 'rxjs';

import { ActivityType, TourLocation } from '../models/lookup.model';
import { Difficulty } from '../models/tour.model';
import { GuidePanelService } from '../services/guide-panel.service';
import { LookupService } from '../services/lookup.service';

type TourFieldErrors = Partial<Record<string, string[]>>;

@Component({
  selector: 'app-new-tour',
  templateUrl: '../pages/new-tour.component.html',
  imports: [ReactiveFormsModule, RouterLink],
})
export class NewTourComponent {
  private readonly panelService = inject(GuidePanelService);
  private readonly lookupService = inject(LookupService);
  private readonly router = inject(Router);

  protected readonly difficulties: Difficulty[] = ['easy', 'moderate', 'challenging'];

  protected readonly locations = toSignal(
    this.lookupService.getLocations().pipe(catchError(() => of([] as TourLocation[]))),
    { initialValue: [] as TourLocation[] },
  );

  protected readonly activityTypes = toSignal(
    this.lookupService.getActivityTypes().pipe(catchError(() => of([] as ActivityType[]))),
    { initialValue: [] as ActivityType[] },
  );

  protected readonly form = inject(FormBuilder).nonNullable.group({
    title: ['', [Validators.required, Validators.maxLength(200)]],
    description: ['', Validators.required],
    activity_type: [0, Validators.min(1)],
    location: [0, Validators.min(1)],
    duration_minutes: [120, [Validators.required, Validators.min(1)]],
    difficulty: ['easy' as Difficulty, Validators.required],
    price: [0, [Validators.required, Validators.min(0)]],
    max_participants: [8, [Validators.required, Validators.min(1)]],
    is_active: [true],
  });

  protected readonly submitting = signal(false);
  protected readonly serverErrors = signal<TourFieldErrors>({});
  protected readonly generalError = signal<string | null>(null);

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.serverErrors.set({});
    this.generalError.set(null);

    const value = this.form.getRawValue();
    this.panelService.createTour({ ...value, price: String(value.price) }).subscribe({
      next: () => this.router.navigate(['/guide']),
      error: (error: HttpErrorResponse) => {
        this.submitting.set(false);
        if (error.status === 400) {
          this.serverErrors.set(error.error as TourFieldErrors);
        } else {
          this.generalError.set('The tour could not be created. Please try again.');
        }
      },
    });
  }

  protected showError(field: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[field];
    return control.touched && control.invalid;
  }
}
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../services/auth.service';

type FieldErrors = Partial<Record<'first_name' | 'last_name' | 'email' | 'password', string[]>>;

@Component({
  selector: 'app-register',
  templateUrl: '../pages/register.component.html',
  imports: [ReactiveFormsModule, RouterLink],
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly form = inject(FormBuilder).nonNullable.group({
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  protected readonly submitting = signal(false);
  protected readonly serverErrors = signal<FieldErrors>({});
  protected readonly generalError = signal<string | null>(null);

  protected readonly returnUrl = this.safeReturnUrl(this.route.snapshot.queryParamMap.get('returnUrl'));

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.serverErrors.set({});
    this.generalError.set(null);

    this.auth.register(this.form.getRawValue()).subscribe({
      next: () => this.router.navigateByUrl(this.returnUrl),
      error: (error: HttpErrorResponse) => {
        this.submitting.set(false);
        if (error.status === 400) {
          this.serverErrors.set(error.error as FieldErrors);
        } else if (error.status === 429) {
          this.generalError.set('Too many attempts. Please wait a minute and try again.');
        } else {
          this.generalError.set('Something went wrong. Please try again.');
        }
      },
    });
  }

  private safeReturnUrl(url: string | null): string {
    return url && url.startsWith('/') && !url.startsWith('//') ? url : '/';
  }
}
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: '../pages/login.component.html',
  imports: [ReactiveFormsModule, RouterLink],
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly returnUrl = this.safeReturnUrl(this.route.snapshot.queryParamMap.get('returnUrl'));

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.errorMessage.set(null);
    const { email, password } = this.form.getRawValue();

    this.auth.login(email, password).subscribe({
      next: () => this.router.navigateByUrl(this.returnUrl),
      error: (error: HttpErrorResponse) => {
        this.submitting.set(false);
        this.errorMessage.set(this.messageFor(error));
      },
    });
  }

  private messageFor(error: HttpErrorResponse): string {
    if (error.status === 401) return 'Email or password is incorrect.';
    if (error.status === 429) return 'Too many attempts. Please wait a minute and try again.';
    return 'Something went wrong. Please try again.';
  }

  private safeReturnUrl(url: string | null): string {
    return url && url.startsWith('/') && !url.startsWith('//') ? url : '/';
  }
}
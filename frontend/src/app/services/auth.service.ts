import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, map, of, switchMap, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { RegisterRequest, TokenPair, User } from '../models/auth.model';

const ACCESS_KEY = 'aurora-access';
const REFRESH_KEY = 'aurora-refresh';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly authUrl = `${environment.apiUrl}/auth`;

  readonly currentUser = signal<User | null>(null);
  readonly isLoggedIn = computed(() => this.currentUser() !== null);

    init(): Observable<unknown> {
    if (!this.getAccessToken()) {
      return of(null);
    }
    return this.loadCurrentUser().pipe(
      catchError(() => {
        this.clearSession();
        return of(null);
      }),
    );
  }

  login(email: string, password: string): Observable<User> {
    return this.http
      .post<TokenPair>(`${this.authUrl}/token/`, { email: email.toLowerCase(), password })
      .pipe(
        tap((tokens) => this.storeTokens(tokens)),
        switchMap(() => this.loadCurrentUser()),
      );
  }

  register(data: RegisterRequest): Observable<User> {
    return this.http.post<TokenPair>(`${this.authUrl}/register/`, data).pipe(
      tap((tokens) => this.storeTokens(tokens)),
      switchMap(() => this.loadCurrentUser()),
    );
  }

  logout(): void {
    this.clearSession();
    this.router.navigate(['/']);
  }

  refreshAccessToken(): Observable<string> {
    return this.http
      .post<{ access: string }>(`${this.authUrl}/token/refresh/`, { refresh: this.getRefreshToken() })
      .pipe(
        map((response) => response.access),
        tap((access) => localStorage.setItem(ACCESS_KEY, access)),
      );
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  clearSession(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    this.currentUser.set(null);
  }

  private loadCurrentUser(): Observable<User> {
    return this.http.get<User>(`${this.authUrl}/me/`).pipe(tap((user) => this.currentUser.set(user)));
  }

  private storeTokens(tokens: TokenPair): void {
    localStorage.setItem(ACCESS_KEY, tokens.access);
    localStorage.setItem(REFRESH_KEY, tokens.refresh);
  }
}
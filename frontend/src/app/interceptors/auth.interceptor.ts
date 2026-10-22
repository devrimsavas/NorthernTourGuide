import { HttpErrorResponse, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, of, switchMap, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import { AuthService } from '../services/auth.service';

const NO_AUTH_PATHS = ['/auth/token/', '/auth/token/refresh/', '/auth/register/'];

function withToken(request: HttpRequest<unknown>, token: string | null): HttpRequest<unknown> {
  return token ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : request;
}

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);

  const isApiRequest = request.url.startsWith(environment.apiUrl);
  const skipAuth = NO_AUTH_PATHS.some((path) => request.url.endsWith(path));
  if (!isApiRequest || skipAuth) {
    return next(request);
  }

  return next(withToken(request, auth.getAccessToken())).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401 || !auth.getRefreshToken()) {
        return throwError(() => error);
      }

      return auth.refreshAccessToken().pipe(
        catchError(() => {
          auth.clearSession();
          return of(null);
        }),
        switchMap((access) => next(withToken(request, access))),
      );
    }),
  );
};
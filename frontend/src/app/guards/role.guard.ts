import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Role } from '../models/auth.model';
import { AuthService } from '../services/auth.service';

export function roleGuard(role: Role): CanActivateFn {
  return (_route, state) => {
    const auth = inject(AuthService);
    const router = inject(Router);
    const user = auth.currentUser();

    if (!user) {
      return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
    }
    if (user.role !== role) {
      return router.createUrlTree(['/']);
    }
    return true;
  };
}

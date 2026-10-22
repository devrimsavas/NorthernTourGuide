import { Routes } from '@angular/router';
import { HomeComponent } from './components/home.component';
import { ToursComponent } from './components/tours.component';
import { TourDetailComponent } from './components/tour-detail.component';
import { LoginComponent } from './components/login.component';
import { RegisterComponent } from './components/register.component';
import { MyBookingsComponent } from './components/my-bookings.component';
import { roleGuard } from './guards/role.guard';
import { GuidesComponent } from './components/guides.component';
import { GuidePanelComponent } from './components/guide-panel.component';
import { NewTourComponent } from './components/new-tour.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'tours', component: ToursComponent },
  { path: 'tours/:id', component: TourDetailComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'my-bookings', component: MyBookingsComponent, canActivate: [roleGuard('customer')] },
  { path: 'guides', component: GuidesComponent },
  { path: 'guide', component: GuidePanelComponent, canActivate: [roleGuard('guide')] },
  { path: 'guide/tours/new', component: NewTourComponent, canActivate: [roleGuard('guide')] },
];

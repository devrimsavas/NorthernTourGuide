import { BookingStatus } from './booking.model';
import { Difficulty } from './tour.model';

export interface GuideTour {
  id: number;
  title: string;
  description: string;
  activity_type: number;
  location: number;
  duration_minutes: number;
  difficulty: Difficulty;
  price: string;
  max_participants: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type GuideTourInput = Omit<GuideTour, 'id' | 'created_at' | 'updated_at'>;

export interface GuideBooking {
  reference: string;
  tour: string;
  slot: number;
  start_time: string;
  customer_name: string;
  customer_email: string;
  participants: number;
  status: BookingStatus;
  created_at: string;
}
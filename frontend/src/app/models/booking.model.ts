export type BookingStatus = 'pending' | 'confirmed' | 'cancelled';

export interface CreatedBooking {
  reference: string;
  slot: number;
  participants: number;
  total_price: string;
  status: BookingStatus;
  created_at: string;
}

export interface MyBooking {
  reference: string;
  tour: string;
  start_time: string;
  participants: number;
  total_price: string;
  status: BookingStatus;
  created_at: string;
  has_review: boolean;
  can_review: boolean;
  can_cancel: boolean;
}

export interface ReviewRequest {
  rating: number;
  comment: string;
}
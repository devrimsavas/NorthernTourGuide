export type Difficulty = 'easy' | 'moderate' | 'challenging';

export interface Tour {
  id: number;
  title: string;
  description: string;
  guide: string;
  activity_type: string;
  location: string;
  duration_minutes: number;
  difficulty: Difficulty;
  price: string;
  max_participants: number;
  average_rating: number | null;
  review_count: number;
  cover_image: string | null;
}

export interface TourSlot {
  id: number;
  start_time: string;
  available_spots: number;
}

export interface TourImage {
  image: string;
  alt_text: string;
}

export interface TourDetail extends Tour {
  slots: TourSlot[];
  images: TourImage[];
}
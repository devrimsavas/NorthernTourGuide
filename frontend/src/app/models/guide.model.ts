export interface Guide {
  id: number;
  first_name: string;
  last_name: string;
  bio: string;
  languages: string;
  years_of_experience: number;
  base_location: string | null;
  photo: string | null;
}
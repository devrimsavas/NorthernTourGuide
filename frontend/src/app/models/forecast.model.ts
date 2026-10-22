export type AuroraChance = 'low' | 'medium' | 'high';

export interface WeatherForecast {
  time: string;
  air_temperature: number | null;
  cloud_area_fraction: number | null;
  wind_speed: number | null;
  symbol_code: string | null;
}

export interface AuroraForecast {
  kp: number;
  chance: AuroraChance | null;
}

export interface SlotForecast {
  slot_id: number;
  start_time: string;
  forecast: WeatherForecast | null;
  aurora: AuroraForecast | null;
}

export interface TourForecast {
  location: string;
  sources: string[];
  slots: SlotForecast[];
}
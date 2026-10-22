export type Role = 'customer' | 'guide' | 'admin';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface RegisterRequest {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}
export type Style =
  | "scandinavian"
  | "minimalist"
  | "industrial"
  | "bohemian"
  | "modern_indian"
  | "traditional_indian"
  | "mid_century"
  | "coastal";

export interface StyleOption {
  value: Style;
  label: string;
  swatch: string; // representative color
}

export const STYLES: StyleOption[] = [
  { value: "scandinavian", label: "Scandinavian", swatch: "#E8E2D6" },
  { value: "minimalist", label: "Minimalist", swatch: "#F4F4F2" },
  { value: "industrial", label: "Industrial", swatch: "#6B6B6B" },
  { value: "bohemian", label: "Bohemian", swatch: "#C06B3E" },
  { value: "modern_indian", label: "Modern Indian", swatch: "#B33A3A" },
  { value: "traditional_indian", label: "Traditional Indian", swatch: "#A6761D" },
  { value: "mid_century", label: "Mid-Century", swatch: "#D98E3A" },
  { value: "coastal", label: "Coastal", swatch: "#9CC3D5" },
];

export interface User {
  id: number;
  email: string;
  plan: "free" | "pro";
  credits_remaining: number;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DetectedObject {
  label: string;
  location?: string | null;
  confidence?: string | null;
}

export interface PaletteColor {
  hex: string;
  name: string;
  usage: string;
}

export interface FurnitureSuggestion {
  category: string;
  description: string;
  placement_note: string;
  est_price_range_inr: string;
}

export interface Design {
  id: number;
  room_id: number;
  style: string;
  status: "pending" | "complete" | "failed";
  room_type?: string | null;
  image_url?: string | null;
  detected_objects?: DetectedObject[] | null;
  palette?: PaletteColor[] | null;
  furniture_suggestions?: FurnitureSuggestion[] | null;
  layout_notes?: string | null;
  created_at: string;
}

export interface RoomUploadResponse {
  room_id: number;
  image_url: string;
}

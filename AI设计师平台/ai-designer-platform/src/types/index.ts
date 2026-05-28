export interface BrandProfile {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  logo_url: string;
  style_keywords: string[];
  restrictions: string[];
}

export interface Project {
  id: string;
  name: string;
  description: string;
  brand_profile: BrandProfile;
}

export interface ContentType {
  id: string;
  name: string;
  icon: string;
}

export interface StylePreference {
  id: string;
  name: string;
}

export interface AspectRatio {
  id: string;
  name: string;
  width: number | null;
  height: number | null;
}

export interface AIPlatform {
  id: string;
  name: string;
  icon: string;
}

export interface SpecialRequirement {
  id: string;
  name: string;
}

export interface GenerationRequest {
  projectId: string;
  contentType: string;
  keywords: string[];
  stylePreferences: string[];
  aspectRatio: string;
  customWidth?: number;
  customHeight?: number;
  specialRequirements: string[];
  description: string;
  aiPlatform: string;
  prompt: string;
}

export interface GeneratedImage {
  id: string;
  url: string;
  prompt: string;
  timestamp: Date;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  contentType: string;
  stylePreferences: string[];
  keywords: string[];
  aspectRatio: string;
  specialRequirements: string[];
  promptTemplate: string;
}

export interface BrandProfilesData {
  projects: Project[];
  content_types: ContentType[];
  style_preferences: StylePreference[];
  aspect_ratios: AspectRatio[];
  ai_platforms: AIPlatform[];
  special_requirements: SpecialRequirement[];
}

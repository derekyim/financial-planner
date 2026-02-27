export const APP_NAME = 'Dysprosium Financial Assistant';
export const APP_SHORT_NAME = 'Dysprosium AI';
export const BRAND_NAME = 'Dysprosium';

export const PROJECT_NAME = 'Powdered Drink City';
export const PROJECT_SUBTITLE = 'AI-Powered Financial Planning & Analysis for Ecommerce Businesses';

export const EMBEDDING_MODEL = 'text-embedding-3-small';
export const EMBEDDING_DIMS = 1536;
export const CHUNK_SIZE = 500;
export const CHUNK_OVERLAP = 50;
export const RETRIEVAL_K = 5;

export const SUPERVISOR_MODEL = 'GPT-4o';
export const AGENT_MODEL = 'GPT-4o-mini';

export const TOUR_STORAGE_KEY = 'dys-tour-completed';
export const MODELS_STORAGE_KEY = 'dys-saved-models';

export type SavedModel = {
  name: string;
  url: string;
};

export const DEFAULT_MODEL: SavedModel = {
  name: 'Powdered Drink City',
  url: process.env.NEXT_PUBLIC_SPREADSHEET_URL || '',
};

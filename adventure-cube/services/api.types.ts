/**
 * Backend API types matching Django models
 */

export interface StoryParagraph {
    id: string;
    paragraph_index: number;
    paragraph_type: 'intro_goal' | 'problem_obstacle' | 'effort_effort' | 'climax_climax' | 'ending_ending';
    text: string;
    tts_url?: string;
    tts_duration_seconds?: number;
    is_generated: boolean;
    is_ready: boolean;
    generated_at?: string;
}

export interface BackendStory {
    id: string;
    title: string;
    body: string;
    theme: string;
    child_name?: string;
    child_age?: number;
    model_source: 'online' | 'offline';
    language: string;
    character?: string;
    background?: string;
    key_items?: string[];
    generation_status?: 'pending' | 'generating_intro' | 'intro_ready' | 'generating_remaining' | 'completed';
    context_template?: string;
    paragraphs?: StoryParagraph[];
    paragraphs_ready?: number;
    total_paragraphs?: number;
    created_at: string;
}

export interface StoryGenerateRequest {
    title?: string;
    theme: string;
    child_name?: string;
    child_age?: number;
    language?: string;
    character?: string;
    background?: string;
    key_items?: string[];
    context_template?: string;
}

export interface AudioFile {
    id: string;
    story: string;
    language: string;
    audio_url: string;
    duration_seconds?: number;
    created_at: string;
}

export interface TTSGenerateRequest {
    story_id: string;
    language?: string;
    voice?: string;
}

export interface ImageAsset {
    name: string;
    filename: string;
    path: string;
    category: 'characters' | 'backgrounds' | 'themes' | 'key_items';
}

export interface ImagesResponse {
    characters: ImageAsset[];
    backgrounds: ImageAsset[];
    themes: ImageAsset[];
    key_items: ImageAsset[];
}

export interface Theme {
    id: string;
    name: string;
    description: string;
    story_count: number;
}

export interface ThemesResponse {
    themes: Theme[];
}

export interface ApiError {
    error: string;
    details?: any;
}

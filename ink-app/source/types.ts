/**
 * Core types for Janett tutorial system
 */

export type Provider = 'openai' | 'anthropic' | 'ollama';

export type ModelInfo = {
	name: string;
	provider: Provider;
	displayName: string;
};

export type Chapter = {
	id: number;
	title: string;
	summary: string;
	content: string;
};

export type Tutorial = {
	title: string;
	description: string;
	topic: string;
	chapters: Chapter[];
};

export type AppMode = 'welcome' | 'tutorial' | 'chat' | 'settings';

export type ChatMessage = {
	role: 'user' | 'assistant';
	content: string;
};

export type AppState = {
	mode: AppMode;
	tutorial: Tutorial | null;
	currentChapterIndex: number;
	provider: Provider;
	model: string;
	isGenerating: boolean;
	error: string | null;
	chatMessages: ChatMessage[];
};

export type Config = {
	openaiApiKey?: string;
	anthropicApiKey?: string;
	defaultProvider: Provider;
	defaultModel: string;
};

export type GenerateOptions = {
	topic: string;
	provider: Provider;
	model: string;
	numChapters?: number;
};

export type ContinueOptions = {
	tutorial: Tutorial;
	provider: Provider;
	model: string;
	numChapters?: number;
};

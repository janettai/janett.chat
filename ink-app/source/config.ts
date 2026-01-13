/**
 * Configuration management for Janett
 */

import Conf from 'conf';
import {type Config, type Provider} from './types.js';

// Provider configuration
export const PROVIDERS: Record<
	Provider,
	{name: string; baseUrl: string; defaultModel: string}
> = {
	ollama: {
		name: 'Ollama (Local)',
		baseUrl: 'http://localhost:11434/v1',
		defaultModel: 'llama3.2',
	},
	openai: {
		name: 'OpenAI',
		baseUrl: 'https://api.openai.com/v1',
		defaultModel: 'gpt-4o-mini',
	},
	anthropic: {
		name: 'Anthropic',
		baseUrl: 'https://api.anthropic.com',
		defaultModel: 'claude-3-haiku-20240307',
	},
};

// OpenAI models
export const OPENAI_MODELS = ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'];

// Anthropic models
export const ANTHROPIC_MODELS = [
	'claude-3-haiku-20240307',
	'claude-3-sonnet-20240229',
	'claude-3-opus-20240229',
];

const config = new Conf<Config>({
	projectName: 'janett',
	defaults: {
		defaultProvider: 'ollama',
		defaultModel: 'llama3.2',
	},
});

export function getConfig(): Config {
	return config.store;
}

export function setApiKey(provider: Provider, apiKey: string): void {
	if (provider === 'openai') {
		config.set('openaiApiKey', apiKey);
	} else if (provider === 'anthropic') {
		config.set('anthropicApiKey', apiKey);
	}
}

export function getApiKey(provider: Provider): string | undefined {
	// Check environment variables first
	if (provider === 'openai') {
		return process.env['OPENAI_API_KEY'] ?? config.get('openaiApiKey');
	} else if (provider === 'anthropic') {
		return process.env['ANTHROPIC_API_KEY'] ?? config.get('anthropicApiKey');
	}
	return undefined;
}

export function getOllamaBaseUrl(): string {
	return PROVIDERS.ollama.baseUrl;
}

export function setDefaultProvider(provider: Provider): void {
	config.set('defaultProvider', provider);
	// Also set the default model for this provider
	config.set('defaultModel', PROVIDERS[provider].defaultModel);
}

export function setDefaultModel(model: string): void {
	config.set('defaultModel', model);
}

// Fetch available Ollama models
export async function getOllamaModels(): Promise<string[]> {
	try {
		const response = await fetch('http://localhost:11434/api/tags');
		if (response.ok) {
			const data = (await response.json()) as {models?: Array<{name: string}>};
			const models = (data.models ?? []).map(m => m.name.split(':')[0]!);
			// Remove duplicates
			return [...new Set(models)];
		}
	} catch {
		// Ollama not running or not reachable
	}
	return [];
}

// Check if Ollama is available
export async function isOllamaAvailable(): Promise<boolean> {
	try {
		const response = await fetch('http://localhost:11434/api/tags', {
			signal: AbortSignal.timeout(2000),
		});
		return response.ok;
	} catch {
		return false;
	}
}

export {config};

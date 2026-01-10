/**
 * Configuration management for Janett
 */

import Conf from 'conf';
import {type Config, type Provider} from './types.js';

const config = new Conf<Config>({
	projectName: 'janett',
	defaults: {
		defaultProvider: 'openai',
		defaultModel: 'gpt-4o-mini',
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

export function setDefaultProvider(provider: Provider): void {
	config.set('defaultProvider', provider);
}

export function setDefaultModel(model: string): void {
	config.set('defaultModel', model);
}

export {config};

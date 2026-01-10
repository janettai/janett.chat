/**
 * Model selection component
 */

import React, {useEffect, useState} from 'react';
import {Box, Text} from 'ink';
import SelectInput from 'ink-select-input';
import Spinner from 'ink-spinner';
import {type Provider} from '../types.js';
import {
	PROVIDERS,
	OPENAI_MODELS,
	ANTHROPIC_MODELS,
	getOllamaModels,
} from '../config.js';

type Props = {
	provider: Provider;
	currentModel: string;
	onSelect: (model: string) => void;
	onCancel: () => void;
};

export default function ModelSelect({
	provider,
	currentModel,
	onSelect,
	onCancel: _onCancel,
}: Props) {
	const [models, setModels] = useState<string[]>([]);
	const [loading, setLoading] = useState(false);

	useEffect(() => {
		const loadModels = async () => {
			if (provider === 'ollama') {
				setLoading(true);
				const ollamaModels = await getOllamaModels();
				setModels(
					ollamaModels.length > 0 ? ollamaModels : ['llama3.2', 'llama3.1'],
				);
				setLoading(false);
			} else if (provider === 'openai') {
				setModels(OPENAI_MODELS);
			} else if (provider === 'anthropic') {
				setModels(ANTHROPIC_MODELS);
			}
		};

		loadModels();
	}, [provider]);

	const items = models.map(model => ({
		label: `${model}${model === currentModel ? ' (current)' : ''}`,
		value: model,
	}));

	const handleSelect = (item: {label: string; value: string}) => {
		onSelect(item.value);
	};

	if (loading) {
		return (
			<Box paddingX={2} paddingY={1}>
				<Text color="cyan">
					<Spinner type="dots" />
				</Text>
				<Text> Loading models from Ollama...</Text>
			</Box>
		);
	}

	return (
		<Box flexDirection="column" paddingX={2} paddingY={1}>
			<Box marginBottom={1}>
				<Text bold color="cyan">
					Select Model for {PROVIDERS[provider].name}
				</Text>
			</Box>

			<Box marginBottom={1}>
				<Text dimColor>
					Current: <Text color="yellow">{currentModel}</Text>
				</Text>
			</Box>

			{items.length > 0 ? (
				<SelectInput items={items} onSelect={handleSelect} />
			) : (
				<Text color="red">No models available. Is Ollama running?</Text>
			)}

			<Box marginTop={1}>
				<Text dimColor>
					Press <Text color="yellow">ESC</Text> to cancel
				</Text>
			</Box>
		</Box>
	);
}

/**
 * API key input component
 */

import React, {useState} from 'react';
import {Box, Text} from 'ink';
import TextInput from 'ink-text-input';
import {type Provider} from '../types.js';
import {PROVIDERS, getApiKey} from '../config.js';

type Props = {
	provider: Provider;
	onSubmit: (apiKey: string) => void;
	onCancel: () => void;
};

export default function ApiKeyInput({provider, onSubmit, onCancel}: Props) {
	const [value, setValue] = useState('');
	const currentKey = getApiKey(provider);
	const maskedKey = currentKey
		? `${currentKey.slice(0, 8)}...${currentKey.slice(-4)}`
		: undefined;

	const handleSubmit = (input: string) => {
		if (input.trim()) {
			onSubmit(input.trim());
		} else {
			onCancel();
		}
	};

	if (provider === 'ollama') {
		return (
			<Box flexDirection="column" paddingX={2} paddingY={1}>
				<Text color="yellow">
					Ollama doesn&apos;t require an API key - it runs locally.
				</Text>
				<Box marginTop={1}>
					<Text dimColor>Press Enter to continue...</Text>
				</Box>
			</Box>
		);
	}

	return (
		<Box flexDirection="column" paddingX={2} paddingY={1}>
			<Box marginBottom={1}>
				<Text bold color="cyan">
					Set API Key for {PROVIDERS[provider].name}
				</Text>
			</Box>

			{maskedKey && (
				<Box marginBottom={1}>
					<Text dimColor>
						Current key: <Text color="yellow">{maskedKey}</Text>
					</Text>
				</Box>
			)}

			<Box>
				<Text color="yellow">API Key: </Text>
				<TextInput
					value={value}
					onChange={setValue}
					onSubmit={handleSubmit}
					placeholder="Enter your API key..."
					mask="*"
				/>
			</Box>

			<Box marginTop={1}>
				<Text dimColor>
					Press <Text color="yellow">Enter</Text> to save, or leave empty to
					cancel
				</Text>
			</Box>
		</Box>
	);
}

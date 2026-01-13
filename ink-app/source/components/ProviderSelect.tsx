/**
 * Provider selection component
 */

import React from 'react';
import {Box, Text} from 'ink';
import SelectInput from 'ink-select-input';
import {type Provider} from '../types.js';
import {PROVIDERS} from '../config.js';

type Props = {
	currentProvider: Provider;
	onSelect: (provider: Provider) => void;
	onCancel: () => void;
};

export default function ProviderSelect({
	currentProvider,
	onSelect,
	onCancel: _onCancel,
}: Props) {
	const items = (
		Object.entries(PROVIDERS) as Array<[Provider, (typeof PROVIDERS)['ollama']]>
	).map(([key, value]) => ({
		label: `${value.name}${key === currentProvider ? ' (current)' : ''}`,
		value: key,
	}));

	const handleSelect = (item: {label: string; value: Provider}) => {
		onSelect(item.value);
	};

	return (
		<Box flexDirection="column" paddingX={2} paddingY={1}>
			<Box marginBottom={1}>
				<Text bold color="cyan">
					Select AI Provider
				</Text>
			</Box>

			<Box marginBottom={1}>
				<Text dimColor>
					Current: <Text color="yellow">{PROVIDERS[currentProvider].name}</Text>
				</Text>
			</Box>

			<SelectInput items={items} onSelect={handleSelect} />

			<Box marginTop={1}>
				<Text dimColor>
					Press <Text color="yellow">ESC</Text> to cancel
				</Text>
			</Box>
		</Box>
	);
}

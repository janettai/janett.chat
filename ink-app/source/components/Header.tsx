/**
 * Header component - Claude Code inspired minimal header
 */

import React from 'react';
import {Box, Text} from 'ink';
import Gradient from 'ink-gradient';
import {type Provider} from '../types.js';

type Props = {
	mode: 'tutorial' | 'chat' | 'welcome' | 'settings';
	provider: Provider;
	model: string;
	chapterInfo?: string; // e.g., "Ch 2/5"
};

export default function Header({mode, provider, model, chapterInfo}: Props) {
	const modeDisplay = mode === 'tutorial' ? 'Tutorial' : mode === 'chat' ? 'Chat' : 'Welcome';
	const providerDisplay = provider === 'openai' ? 'OpenAI' : provider === 'anthropic' ? 'Anthropic' : 'Ollama';

	return (
		<Box flexDirection="column" marginBottom={1}>
			<Box>
				<Gradient name="passion">
					<Text bold> Janett </Text>
				</Gradient>
				<Text dimColor> • </Text>
				<Text color="cyan">{modeDisplay}</Text>
				<Text dimColor> • </Text>
				<Text color="gray">{providerDisplay}</Text>
				<Text dimColor> / </Text>
				<Text color="gray">{model}</Text>
				{chapterInfo && (
					<>
						<Text dimColor> • </Text>
						<Text color="yellow">{chapterInfo}</Text>
					</>
				)}
			</Box>
			<Box>
				<Text dimColor>{'─'.repeat(80)}</Text>
			</Box>
		</Box>
	);
}

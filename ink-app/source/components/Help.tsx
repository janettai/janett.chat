/**
 * Help component showing available commands
 */

import React from 'react';
import {Box, Text} from 'ink';
import {type AppMode} from '../types.js';

type Props = {
	mode: AppMode;
};

type CommandInfo = {
	command: string;
	description: string;
};

const globalCommands: CommandInfo[] = [
	{command: '/help', description: 'Show this help message'},
	{command: '/quit, /q', description: 'Exit Janett'},
];

const tutorialCommands: CommandInfo[] = [
	{command: '/next, /n', description: 'Go to next chapter'},
	{command: '/prev, /p', description: 'Go to previous chapter'},
	{command: '/chapters, /c', description: 'View all chapters'},
	{command: '/goto [N]', description: 'Jump to chapter N'},
	{command: '/more', description: 'Generate more chapters'},
	{command: '/topic [text]', description: 'Start new tutorial'},
	{command: '/chat', description: 'Switch to chat mode'},
];

const chatCommands: CommandInfo[] = [
	{command: '/back', description: 'Return to tutorial'},
	{command: '/clear', description: 'Clear chat history'},
];

const settingsCommands: CommandInfo[] = [
	{command: '/provider', description: 'Switch AI provider'},
	{command: '/model', description: 'Change model'},
	{command: '/apikey', description: 'Set API key'},
];

function CommandList({
	title,
	commands,
}: {
	title: string;
	commands: CommandInfo[];
}) {
	return (
		<Box flexDirection="column" marginBottom={1}>
			<Text bold color="cyan">
				{title}
			</Text>
			{commands.map((cmd, idx) => (
				<Box key={idx} marginLeft={2}>
					<Box width={20}>
						<Text color="yellow">{cmd.command}</Text>
					</Box>
					<Text dimColor>{cmd.description}</Text>
				</Box>
			))}
		</Box>
	);
}

export default function Help({mode}: Props) {
	return (
		<Box flexDirection="column" paddingX={2} paddingY={1}>
			<Box marginBottom={1}>
				<Text bold color="yellow">
					Janett Help
				</Text>
			</Box>

			{/* Context-specific commands */}
			{mode === 'tutorial' && (
				<CommandList title="Tutorial Commands" commands={tutorialCommands} />
			)}

			{mode === 'chat' && (
				<CommandList title="Chat Commands" commands={chatCommands} />
			)}

			{/* Settings commands available in all modes */}
			<CommandList title="Settings" commands={settingsCommands} />

			{/* Global commands */}
			<CommandList title="General" commands={globalCommands} />

			<Box marginTop={1}>
				<Text dimColor>
					Press <Text color="yellow">ESC</Text> or type{' '}
					<Text color="yellow">/back</Text> to close help
				</Text>
			</Box>
		</Box>
	);
}

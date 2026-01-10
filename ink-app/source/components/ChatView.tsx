/**
 * Chat view component with message history and streaming support
 */

import React from 'react';
import {Box, Text} from 'ink';
import Spinner from 'ink-spinner';
import {type ChatMessage} from '../types.js';

type Props = {
	messages: ChatMessage[];
	isStreaming: boolean;
	streamingContent: string;
	tutorialContext?: string; // Optional context from tutorial
};

// Simple markdown renderer for chat messages
function renderMarkdown(text: string): JSX.Element[] {
	const elements: JSX.Element[] = [];
	const lines = text.split('\n');
	let inCodeBlock = false;
	let codeLines: string[] = [];
	let codeLanguage = '';
	let keyIdx = 0;

	for (const line of lines) {
		// Code block handling
		if (line.startsWith('```')) {
			if (!inCodeBlock) {
				inCodeBlock = true;
				codeLanguage = line.replace('```', '').trim();
				codeLines = [];
			} else {
				inCodeBlock = false;
				elements.push(
					<Box
						key={keyIdx++}
						flexDirection="column"
						marginY={1}
						borderStyle="round"
						borderColor="green"
						paddingX={2}
						paddingY={1}
					>
						{codeLanguage && (
							<Text color="cyan" dimColor>
								{codeLanguage}
							</Text>
						)}
						<Text color="green">{codeLines.join('\n')}</Text>
					</Box>,
				);
				codeLines = [];
				codeLanguage = '';
			}
			continue;
		}

		if (inCodeBlock) {
			codeLines.push(line);
			continue;
		}

		// Regular text with inline formatting
		if (!line.trim()) {
			elements.push(<Text key={keyIdx++}> </Text>);
		} else if (line.startsWith('# ')) {
			elements.push(
				<Text key={keyIdx++} bold color="yellow">
					{line.replace(/^#\s*/, '')}
				</Text>,
			);
		} else if (line.startsWith('## ')) {
			elements.push(
				<Text key={keyIdx++} bold color="cyan">
					{line.replace(/^##\s*/, '')}
				</Text>,
			);
		} else if (line.startsWith('- ') || line.startsWith('* ')) {
			elements.push(
				<Box key={keyIdx++} marginLeft={2}>
					<Text color="cyan">{'  '}. </Text>
					<Text>{line.replace(/^[-*]\s*/, '')}</Text>
				</Box>,
			);
		} else {
			elements.push(<Text key={keyIdx++}>{line}</Text>);
		}
	}

	// Handle unclosed code block
	if (inCodeBlock && codeLines.length > 0) {
		elements.push(
			<Box
				key={keyIdx++}
				flexDirection="column"
				marginY={1}
				borderStyle="round"
				borderColor="green"
				paddingX={2}
				paddingY={1}
			>
				{codeLanguage && (
					<Text color="cyan" dimColor>
						{codeLanguage}
					</Text>
				)}
				<Text color="green">{codeLines.join('\n')}</Text>
			</Box>,
		);
	}

	return elements;
}

export default function ChatView({
	messages,
	isStreaming,
	streamingContent,
	tutorialContext,
}: Props) {
	return (
		<Box flexDirection="column" paddingX={2} paddingY={1}>
			{/* Tutorial context hint */}
			{tutorialContext && messages.length === 0 && (
				<Box marginBottom={1}>
					<Text dimColor>
						Chatting about: <Text color="cyan">{tutorialContext}</Text>
					</Text>
				</Box>
			)}

			{/* Welcome message if no messages */}
			{messages.length === 0 && !isStreaming && (
				<Box flexDirection="column" marginY={1}>
					<Text bold>Hello! </Text>
					<Text dimColor>How can I help you today?</Text>
					<Box marginTop={1}>
						<Text dimColor>
							Type a message to start chatting, or{' '}
							<Text color="yellow">/back</Text> to return to the tutorial.
						</Text>
					</Box>
				</Box>
			)}

			{/* Message history */}
			{messages.map((msg, idx) => (
				<Box key={idx} flexDirection="column" marginBottom={1}>
					{msg.role === 'user' ? (
						<>
							<Text bold color="cyan">
								You
							</Text>
							<Box marginLeft={2}>
								<Text>{msg.content}</Text>
							</Box>
						</>
					) : (
						<>
							<Text bold color="yellow">
								Janett
							</Text>
							<Box flexDirection="column" marginLeft={2}>
								{renderMarkdown(msg.content)}
							</Box>
						</>
					)}
				</Box>
			))}

			{/* Streaming response */}
			{isStreaming && (
				<Box flexDirection="column" marginBottom={1}>
					<Text bold color="yellow">
						Janett
					</Text>
					<Box flexDirection="column" marginLeft={2}>
						{streamingContent ? (
							renderMarkdown(streamingContent)
						) : (
							<Box>
								<Text color="cyan">
									<Spinner type="dots" />
								</Text>
								<Text dimColor> Thinking...</Text>
							</Box>
						)}
					</Box>
				</Box>
			)}
		</Box>
	);
}

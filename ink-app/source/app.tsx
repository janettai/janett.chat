/**
 * Main Janett application component
 */

import React, {useState, useCallback} from 'react';
import {Box, Text, useInput, useApp} from 'ink';
import Header from './components/Header.js';
import Welcome from './components/Welcome.js';
import ChapterView from './components/ChapterView.js';
import ChapterList from './components/ChapterList.js';
import ChatView from './components/ChatView.js';
import Loading from './components/Loading.js';
import Input from './components/Input.js';
import Help from './components/Help.js';
import ProviderSelect from './components/ProviderSelect.js';
import ModelSelect from './components/ModelSelect.js';
import ApiKeyInput from './components/ApiKeyInput.js';
import {
	type Tutorial,
	type AppMode,
	type Provider,
	type ChatMessage,
} from './types.js';
import {generateTutorial, generateMoreChapters, streamChat} from './ai.js';
import {
	getConfig,
	setApiKey,
	setDefaultProvider,
	setDefaultModel,
	PROVIDERS,
} from './config.js';

type ViewMode = 'chapter' | 'list' | 'help' | 'provider' | 'model' | 'apikey';

export default function App() {
	const {exit} = useApp();
	const config = getConfig();

	// Core state
	const [mode, setMode] = useState<AppMode>('welcome');
	const [viewMode, setViewMode] = useState<ViewMode>('chapter');
	const [tutorial, setTutorial] = useState<Tutorial | null>(null);
	const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
	const [provider, setProvider] = useState<Provider>(config.defaultProvider);
	const [model, setModel] = useState(config.defaultModel);
	const [isGenerating, setIsGenerating] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [userInput, setUserInput] = useState('');

	// Chat state
	const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
	const [isStreaming, setIsStreaming] = useState(false);
	const [streamingContent, setStreamingContent] = useState('');

	// Success message state
	const [successMessage, setSuccessMessage] = useState<string | null>(null);

	// Show success message temporarily
	const showSuccess = useCallback((message: string) => {
		setSuccessMessage(message);
		setTimeout(() => setSuccessMessage(null), 3000);
	}, []);

	// Generate a new tutorial
	const handleGenerateTutorial = async (topic: string) => {
		setIsGenerating(true);
		setError(null);
		try {
			const newTutorial = await generateTutorial(topic, provider, model);
			setTutorial(newTutorial);
			setCurrentChapterIndex(0);
			setMode('tutorial');
			setViewMode('chapter');
		} catch (err) {
			setError(
				err instanceof Error ? err.message : 'Failed to generate tutorial',
			);
		} finally {
			setIsGenerating(false);
		}
	};

	// Generate more chapters
	const handleGenerateMore = async () => {
		if (!tutorial) return;
		setIsGenerating(true);
		setError(null);
		try {
			const newChapters = await generateMoreChapters(
				tutorial,
				provider,
				model,
				3,
			);
			setTutorial({
				...tutorial,
				chapters: [...tutorial.chapters, ...newChapters],
			});
			setCurrentChapterIndex(tutorial.chapters.length);
			showSuccess(`Added ${newChapters.length} new chapters!`);
		} catch (err) {
			setError(
				err instanceof Error ? err.message : 'Failed to generate more chapters',
			);
		} finally {
			setIsGenerating(false);
		}
	};

	// Handle chat message
	const handleChatMessage = async (message: string) => {
		// Add user message
		const userMsg: ChatMessage = {role: 'user', content: message};
		setChatMessages(prev => [...prev, userMsg]);
		setIsStreaming(true);
		setStreamingContent('');

		try {
			let fullResponse = '';
			for await (const chunk of streamChat(
				message,
				provider,
				model,
				chatMessages,
			)) {
				fullResponse += chunk;
				setStreamingContent(fullResponse);
			}

			// Add assistant message
			const assistantMsg: ChatMessage = {
				role: 'assistant',
				content: fullResponse,
			};
			setChatMessages(prev => [...prev, assistantMsg]);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Failed to get response');
			// Remove the user message on error
			setChatMessages(prev => prev.slice(0, -1));
		} finally {
			setIsStreaming(false);
			setStreamingContent('');
		}
	};

	// Command handler
	const handleCommand = async (input: string) => {
		const trimmed = input.trim();

		if (!trimmed) return;

		// Global commands (work in any mode)
		if (trimmed === '/quit' || trimmed === '/exit' || trimmed === '/q') {
			exit();
			return;
		}

		if (trimmed === '/help' || trimmed === '/?') {
			setViewMode('help');
			return;
		}

		if (trimmed === '/provider') {
			setViewMode('provider');
			return;
		}

		if (trimmed === '/model' || trimmed === '/models') {
			setViewMode('model');
			return;
		}

		if (trimmed === '/apikey') {
			setViewMode('apikey');
			return;
		}

		if (trimmed === '/back' || trimmed === '/b') {
			if (
				viewMode === 'help' ||
				viewMode === 'provider' ||
				viewMode === 'model' ||
				viewMode === 'apikey'
			) {
				setViewMode('chapter');
				return;
			}
			if (mode === 'chat') {
				setMode('tutorial');
				setViewMode('chapter');
				return;
			}
			if (viewMode === 'list') {
				setViewMode('chapter');
				return;
			}
		}

		// Chat mode commands
		if (mode === 'chat') {
			if (trimmed === '/clear') {
				setChatMessages([]);
				showSuccess('Chat history cleared');
				return;
			}

			// Otherwise, it's a chat message
			if (!trimmed.startsWith('/')) {
				await handleChatMessage(trimmed);
				return;
			}
		}

		// Tutorial mode commands
		if (mode === 'tutorial' && tutorial) {
			if (trimmed === '/next' || trimmed === '/n') {
				if (currentChapterIndex < tutorial.chapters.length - 1) {
					setCurrentChapterIndex(prev => prev + 1);
					setViewMode('chapter');
				} else {
					setError('Already at the last chapter. Use /more to generate more.');
				}
				return;
			}

			if (trimmed === '/prev' || trimmed === '/p') {
				if (currentChapterIndex > 0) {
					setCurrentChapterIndex(prev => prev - 1);
					setViewMode('chapter');
				} else {
					setError('Already at the first chapter.');
				}
				return;
			}

			if (trimmed === '/chapters' || trimmed === '/c') {
				setViewMode('list');
				return;
			}

			if (trimmed.startsWith('/goto ') || trimmed.startsWith('/g ')) {
				const chapterNum = parseInt(trimmed.split(' ')[1] ?? '', 10);
				if (
					!isNaN(chapterNum) &&
					chapterNum >= 1 &&
					chapterNum <= tutorial.chapters.length
				) {
					setCurrentChapterIndex(chapterNum - 1);
					setViewMode('chapter');
				} else {
					setError(`Invalid chapter. Use 1-${tutorial.chapters.length}`);
				}
				return;
			}

			if (trimmed === '/more' || trimmed === '/m') {
				await handleGenerateMore();
				return;
			}

			if (trimmed === '/chat') {
				setMode('chat');
				return;
			}

			if (trimmed === '/new') {
				setMode('welcome');
				setTutorial(null);
				setCurrentChapterIndex(0);
				setChatMessages([]);
				return;
			}

			// /topic command to start a new tutorial
			if (trimmed.startsWith('/topic ')) {
				const topic = trimmed.replace('/topic ', '').trim();
				if (topic) {
					setTutorial(null);
					setCurrentChapterIndex(0);
					await handleGenerateTutorial(topic);
				}
				return;
			}
		}

		// Welcome mode - treat input as a topic
		if (mode === 'welcome' && !trimmed.startsWith('/')) {
			await handleGenerateTutorial(trimmed);
			return;
		}

		// Unknown command
		if (trimmed.startsWith('/')) {
			setError(
				`Unknown command: ${trimmed}. Type /help for available commands.`,
			);
		}
	};

	const handleSubmit = async (value: string) => {
		setError(null); // Clear any previous errors
		await handleCommand(value);
		setUserInput('');
	};

	// Handle provider selection
	const handleProviderSelect = (newProvider: Provider) => {
		setProvider(newProvider);
		setModel(PROVIDERS[newProvider].defaultModel);
		setDefaultProvider(newProvider);
		setViewMode('chapter');
		showSuccess(`Switched to ${PROVIDERS[newProvider].name}`);
	};

	// Handle model selection
	const handleModelSelect = (newModel: string) => {
		setModel(newModel);
		setDefaultModel(newModel);
		setViewMode('chapter');
		showSuccess(`Model changed to ${newModel}`);
	};

	// Handle API key submission
	const handleApiKeySubmit = (apiKey: string) => {
		setApiKey(provider, apiKey);
		setViewMode('chapter');
		showSuccess('API key saved');
	};

	// Keyboard shortcuts
	useInput((_input, key) => {
		if (key.escape) {
			if (
				viewMode === 'help' ||
				viewMode === 'provider' ||
				viewMode === 'model' ||
				viewMode === 'apikey'
			) {
				setViewMode('chapter');
			} else if (mode === 'tutorial' && viewMode === 'list') {
				setViewMode('chapter');
			}
		}
	});

	const getChapterInfo = () => {
		if (tutorial) {
			return `Ch ${currentChapterIndex + 1}/${tutorial.chapters.length}`;
		}
		return undefined;
	};

	const getInputPlaceholder = () => {
		if (mode === 'welcome') {
			return 'Enter a topic...';
		}
		if (mode === 'chat') {
			return 'Type a message...';
		}
		return 'Type a command (start with /)...';
	};

	// Determine if input should be disabled
	const inputDisabled =
		isGenerating ||
		isStreaming ||
		viewMode === 'provider' ||
		viewMode === 'model' ||
		viewMode === 'apikey';

	return (
		<Box flexDirection="column">
			{/* Header */}
			{mode !== 'welcome' && (
				<Header
					mode={mode}
					provider={provider}
					model={model}
					chapterInfo={getChapterInfo()}
				/>
			)}

			{/* Error message */}
			{error && (
				<Box paddingX={2}>
					<Text color="red">
						{'  '} {error}
					</Text>
				</Box>
			)}

			{/* Success message */}
			{successMessage && (
				<Box paddingX={2}>
					<Text color="green">
						{'  '} {successMessage}
					</Text>
				</Box>
			)}

			{/* Main content */}
			{!isGenerating && viewMode === 'help' && <Help mode={mode} />}

			{!isGenerating && viewMode === 'provider' && (
				<ProviderSelect
					currentProvider={provider}
					onSelect={handleProviderSelect}
					onCancel={() => setViewMode('chapter')}
				/>
			)}

			{!isGenerating && viewMode === 'model' && (
				<ModelSelect
					provider={provider}
					currentModel={model}
					onSelect={handleModelSelect}
					onCancel={() => setViewMode('chapter')}
				/>
			)}

			{!isGenerating && viewMode === 'apikey' && (
				<ApiKeyInput
					provider={provider}
					onSubmit={handleApiKeySubmit}
					onCancel={() => setViewMode('chapter')}
				/>
			)}

			{!isGenerating &&
				mode === 'welcome' &&
				viewMode !== 'help' &&
				viewMode !== 'provider' &&
				viewMode !== 'model' &&
				viewMode !== 'apikey' && <Welcome />}

			{!isGenerating &&
				mode === 'tutorial' &&
				tutorial &&
				viewMode !== 'help' &&
				viewMode !== 'provider' &&
				viewMode !== 'model' &&
				viewMode !== 'apikey' && (
					<>
						{viewMode === 'chapter' && (
							<ChapterView
								chapter={tutorial.chapters[currentChapterIndex]!}
								currentIndex={currentChapterIndex}
								totalChapters={tutorial.chapters.length}
							/>
						)}
						{viewMode === 'list' && (
							<ChapterList
								tutorial={tutorial}
								currentIndex={currentChapterIndex}
							/>
						)}
					</>
				)}

			{!isGenerating &&
				mode === 'chat' &&
				viewMode !== 'help' &&
				viewMode !== 'provider' &&
				viewMode !== 'model' &&
				viewMode !== 'apikey' && (
					<ChatView
						messages={chatMessages}
						isStreaming={isStreaming}
						streamingContent={streamingContent}
						tutorialContext={tutorial?.title}
					/>
				)}

			{/* Bottom bar with hints + input */}
			<Box flexDirection="column" marginTop={1}>
				{/* Hints line */}
				{mode === 'tutorial' && !isGenerating && viewMode === 'chapter' && (
					<Box paddingX={2}>
						<Text dimColor>
							<Text color="gray">/n</Text> next{'  '}
							<Text color="gray">/p</Text> prev{'  '}
							<Text color="gray">/c</Text> chapters{'  '}
							<Text color="gray">/m</Text> more{'  '}
							<Text color="gray">/chat</Text> chat{'  '}
							<Text color="gray">/q</Text> quit
						</Text>
					</Box>
				)}

				{mode === 'chat' && !isStreaming && (
					<Box paddingX={2}>
						<Text dimColor>
							<Text color="gray">/back</Text> tutorial{'  '}
							<Text color="gray">/clear</Text> clear{'  '}
							<Text color="gray">/q</Text> quit
						</Text>
					</Box>
				)}

				{/* Loading indicator */}
				{isGenerating && (
					<Box paddingX={2}>
						<Loading
							message={
								mode === 'welcome'
									? 'Generating tutorial...'
									: 'Generating more chapters...'
							}
						/>
					</Box>
				)}

				{/* Separator */}
				<Box paddingX={2}>
					<Text dimColor>{'─'.repeat(80)}</Text>
				</Box>

				{/* Input - always visible but disabled during generation */}
				<Input
					value={inputDisabled ? '' : userInput}
					onChange={inputDisabled ? () => {} : setUserInput}
					onSubmit={inputDisabled ? () => {} : handleSubmit}
					placeholder={inputDisabled ? 'Please wait...' : getInputPlaceholder()}
				/>
			</Box>
		</Box>
	);
}

/**
 * Main Janett application component
 */

import React, {useState} from 'react';
import {Box, Text, useInput, useApp} from 'ink';
import Header from './components/Header.js';
import Welcome from './components/Welcome.js';
import ChapterView from './components/ChapterView.js';
import ChapterList from './components/ChapterList.js';
import Loading from './components/Loading.js';
import Input from './components/Input.js';
import {type Tutorial, type AppMode, type Provider} from './types.js';
import {generateTutorial, generateMoreChapters} from './ai.js';
import {getConfig} from './config.js';

type ViewMode = 'chapter' | 'list';

export default function App() {
	const {exit} = useApp();
	const config = getConfig();

	const [mode, setMode] = useState<AppMode>('welcome');
	const [viewMode, setViewMode] = useState<ViewMode>('chapter');
	const [tutorial, setTutorial] = useState<Tutorial | null>(null);
	const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
	const [provider] = useState<Provider>(config.defaultProvider);
	const [model] = useState(config.defaultModel);
	const [isGenerating, setIsGenerating] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [userInput, setUserInput] = useState('');

	// Command handler
	const handleCommand = async (input: string) => {
		const trimmed = input.trim();

		if (!trimmed) return;

		// Global commands
		if (trimmed === '/quit' || trimmed === '/exit' || trimmed === '/q') {
			exit();
			return;
		}

		if (trimmed === '/help' || trimmed === '/?') {
			// TODO: Show help
			return;
		}

		// Tutorial mode commands
		if (mode === 'tutorial' && tutorial) {
			if (trimmed === '/next' || trimmed === '/n') {
				if (currentChapterIndex < tutorial.chapters.length - 1) {
					setCurrentChapterIndex(prev => prev + 1);
					setViewMode('chapter');
				}
			} else if (trimmed === '/prev' || trimmed === '/p') {
				if (currentChapterIndex > 0) {
					setCurrentChapterIndex(prev => prev - 1);
					setViewMode('chapter');
				}
			} else if (trimmed === '/chapters' || trimmed === '/c') {
				setViewMode('list');
			} else if (trimmed === '/back' || trimmed === '/b') {
				setViewMode('chapter');
			} else if (trimmed.startsWith('/goto ') || trimmed.startsWith('/g ')) {
				const chapterNum = parseInt(trimmed.split(' ')[1] ?? '', 10);
				if (
					!isNaN(chapterNum) &&
					chapterNum >= 1 &&
					chapterNum <= tutorial.chapters.length
				) {
					setCurrentChapterIndex(chapterNum - 1);
					setViewMode('chapter');
				}
			} else if (trimmed === '/more' || trimmed === '/m') {
				// Generate more chapters
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
				} catch (err) {
					setError(
						err instanceof Error ? err.message : 'Failed to generate more chapters',
					);
				} finally {
					setIsGenerating(false);
				}
			} else if (trimmed === '/chat') {
				setMode('chat');
			} else if (trimmed === '/new') {
				setMode('welcome');
				setTutorial(null);
				setCurrentChapterIndex(0);
			}

			return;
		}

		// Welcome mode - generate tutorial
		if (mode === 'welcome') {
			setIsGenerating(true);
			setError(null);
			try {
				const newTutorial = await generateTutorial(trimmed, provider, model);
				setTutorial(newTutorial);
				setCurrentChapterIndex(0);
				setMode('tutorial');
				setViewMode('chapter');
			} catch (err) {
				setError(err instanceof Error ? err.message : 'Failed to generate tutorial');
			} finally {
				setIsGenerating(false);
			}
		}
	};

	const handleSubmit = async (value: string) => {
		await handleCommand(value);
		setUserInput('');
	};

	// Keyboard shortcuts
	useInput((_input, key) => {
		if (key.escape) {
			if (mode === 'tutorial' && viewMode === 'list') {
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
		return '';
	};

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

			{/* Error */}
			{error && (
				<Box paddingX={2}>
					<Text color="red">✗ {error}</Text>
				</Box>
			)}

			{/* Main content */}
			{!isGenerating && mode === 'welcome' && <Welcome />}

			{!isGenerating && mode === 'tutorial' && tutorial && (
				<>
					{viewMode === 'chapter' && (
						<ChapterView
							chapter={tutorial.chapters[currentChapterIndex]!}
							currentIndex={currentChapterIndex}
							totalChapters={tutorial.chapters.length}
						/>
					)}
					{viewMode === 'list' && (
						<ChapterList tutorial={tutorial} currentIndex={currentChapterIndex} />
					)}
				</>
			)}

			{/* Bottom bar with hints + input */}
			<Box flexDirection="column" marginTop={1}>
				{/* Hints line */}
				{mode === 'tutorial' && !isGenerating && (
					<Box paddingX={2}>
						<Text dimColor>
							<Text color="gray">/n</Text> next  
							<Text color="gray">/p</Text> prev  
							<Text color="gray">/c</Text> chapters  
							<Text color="gray">/m</Text> more  
							<Text color="gray">/q</Text> quit
						</Text>
					</Box>
				)}

				{/* Loading indicator inline */}
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
					value={isGenerating ? '' : userInput}
					onChange={isGenerating ? () => {} : setUserInput}
					onSubmit={isGenerating ? () => {} : handleSubmit}
					placeholder={isGenerating ? 'Please wait...' : getInputPlaceholder()}
				/>
			</Box>
		</Box>
	);
}

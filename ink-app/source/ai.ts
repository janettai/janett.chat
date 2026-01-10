/**
 * AI service using Vercel AI SDK for multi-provider support
 */

import {generateText, streamText} from 'ai';
import {createOpenAI} from '@ai-sdk/openai';
import {createAnthropic} from '@ai-sdk/anthropic';
import {type Provider, type Tutorial, type Chapter} from './types.js';
import {getApiKey, getOllamaBaseUrl} from './config.js';

const TUTORIAL_SYSTEM_PROMPT = `You are an expert educator who creates comprehensive, structured tutorials.

When a user provides a topic, create a tutorial using this EXACT format:

===TUTORIAL===
Title: [Tutorial title here]
Description: [Brief description]

===CHAPTER 1===
Title: [Chapter title]
Summary: [One line summary]
---
[Full chapter content with explanations and examples]
---

===CHAPTER 2===
Title: [Chapter title]
Summary: [One line summary]
---
[Full chapter content]
---

[Continue with more chapters...]

===END===

Guidelines:
- Create 4-6 chapters
- Each chapter should build on previous ones
- Include code examples where relevant using markdown code blocks
- Make content educational and engaging
- The content section between --- markers can be multiple paragraphs

IMPORTANT: Follow the format exactly with ===TUTORIAL===, ===CHAPTER N===, and ===END=== markers.`;

const CONTINUE_SYSTEM_PROMPT = `You are an expert educator continuing a tutorial.

The user has completed these chapters:
{completed_chapters}

Generate {num_chapters} MORE chapters that go deeper into the topic. Start numbering from Chapter {start_num}.

Use this EXACT format:

===CHAPTER {start_num}===
Title: [Chapter title]
Summary: [One line summary]
---
[Full chapter content with explanations and examples]
---

[Continue with more chapters...]

===END===

Guidelines:
- Build on what was already covered
- Go deeper into advanced concepts
- Include practical examples and exercises
- Don't repeat content from previous chapters

IMPORTANT: Start from Chapter {start_num} and follow the format exactly.`;

function getProvider(provider: Provider, model: string) {
	if (provider === 'ollama') {
		// Ollama uses OpenAI-compatible API with no auth required
		const ollama = createOpenAI({
			baseURL: getOllamaBaseUrl(),
			apiKey: 'ollama', // Ollama doesn't require an API key
		});
		return ollama(model) as any;
	}

	const apiKey = getApiKey(provider);

	if (!apiKey) {
		throw new Error(
			`No API key found for ${provider}. Set it in settings or environment variable.`,
		);
	}

	if (provider === 'openai') {
		const openai = createOpenAI({apiKey});
		return openai(model) as any;
	} else if (provider === 'anthropic') {
		const anthropic = createAnthropic({apiKey});
		return anthropic(model) as any;
	}

	throw new Error(`Unsupported provider: ${provider}`);
}

function parseTutorial(response: string): Tutorial {
	const lines = response.split('\n');
	let title = '';
	let description = '';
	const chapters: Chapter[] = [];

	let inTutorial = false;
	let currentChapter: Partial<Chapter> | null = null;
	let inContent = false;
	let contentLines: string[] = [];

	for (const line of lines) {
		if (line.startsWith('===TUTORIAL===')) {
			inTutorial = true;
			continue;
		}

		if (line.startsWith('===END===')) {
			// Save last chapter if exists
			if (currentChapter && inContent) {
				currentChapter.content = contentLines.join('\n').trim();
				chapters.push(currentChapter as Chapter);
			}
			break;
		}

		if (line.match(/===CHAPTER (\d+)===/)) {
			// Save previous chapter
			if (currentChapter && inContent) {
				currentChapter.content = contentLines.join('\n').trim();
				chapters.push(currentChapter as Chapter);
			}

			// Start new chapter
			const match = line.match(/===CHAPTER (\d+)===/);
			const chapterId = match ? parseInt(match[1]!, 10) : chapters.length + 1;
			currentChapter = {id: chapterId, title: '', summary: '', content: ''};
			inContent = false;
			contentLines = [];
			continue;
		}

		if (inTutorial && !currentChapter) {
			if (line.startsWith('Title:')) {
				title = line.replace('Title:', '').trim();
			} else if (line.startsWith('Description:')) {
				description = line.replace('Description:', '').trim();
			}
		}

		if (currentChapter) {
			if (line.startsWith('Title:')) {
				currentChapter.title = line.replace('Title:', '').trim();
			} else if (line.startsWith('Summary:')) {
				currentChapter.summary = line.replace('Summary:', '').trim();
			} else if (line === '---') {
				if (!inContent) {
					inContent = true;
				}
			} else if (inContent) {
				contentLines.push(line);
			}
		}
	}

	return {
		title: title || 'Untitled Tutorial',
		description: description || 'No description',
		topic: title,
		chapters,
	};
}

export async function generateTutorial(
	topic: string,
	provider: Provider,
	model: string,
): Promise<Tutorial> {
	const providerModel = getProvider(provider, model);

	const {text} = await generateText({
		model: providerModel,
		system: TUTORIAL_SYSTEM_PROMPT,
		prompt: `Create a comprehensive tutorial on: ${topic}`,
		maxTokens: 4000,
	});

	return parseTutorial(text);
}

export async function generateMoreChapters(
	tutorial: Tutorial,
	provider: Provider,
	model: string,
	numChapters: number = 3,
): Promise<Chapter[]> {
	const providerModel = getProvider(provider, model);
	const startNum = tutorial.chapters.length + 1;

	const completedChapters = tutorial.chapters
		.map(ch => `- Chapter ${ch.id}: ${ch.title}`)
		.join('\n');

	const systemPrompt = CONTINUE_SYSTEM_PROMPT.replace(
		'{completed_chapters}',
		completedChapters,
	)
		.replace('{num_chapters}', numChapters.toString())
		.replace(/{start_num}/g, startNum.toString());

	const {text} = await generateText({
		model: providerModel,
		system: systemPrompt,
		prompt: `Continue the tutorial on "${tutorial.topic}" with ${numChapters} more advanced chapters.`,
		maxTokens: 4000,
	});

	const parsed = parseTutorial(text);
	return parsed.chapters;
}

export async function* streamChat(
	message: string,
	provider: Provider,
	model: string,
	conversationHistory: Array<{
		role: 'user' | 'assistant';
		content: string;
	}> = [],
) {
	const providerModel = getProvider(provider, model);

	const messages = [
		...conversationHistory.map(msg => ({
			role: msg.role,
			content: msg.content,
		})),
		{role: 'user' as const, content: message},
	];

	const result = await streamText({
		model: providerModel,
		messages,
	});

	for await (const chunk of result.textStream) {
		yield chunk;
	}
}

/**
 * Chapter display component with proper markdown rendering
 */

import React from 'react';
import {Box, Text} from 'ink';
import {type Chapter} from '../types.js';

type Props = {
	chapter: Chapter;
	currentIndex: number;
	totalChapters: number;
};

// Parse inline markdown (bold, italic, code)
function renderInlineMarkdown(text: string): JSX.Element[] {
	const elements: JSX.Element[] = [];
	let remaining = text;
	let keyIdx = 0;

	while (remaining.length > 0) {
		// Inline code: `code`
		const codeMatch = remaining.match(/^`([^`]+)`/);
		if (codeMatch) {
			elements.push(
				<Text key={keyIdx++} color="green" backgroundColor="gray">
					{' '}{codeMatch[1]}{' '}
				</Text>,
			);
			remaining = remaining.slice(codeMatch[0].length);
			continue;
		}

		// Bold: **text**
		const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/);
		if (boldMatch) {
			elements.push(
				<Text key={keyIdx++} bold>
					{boldMatch[1]}
				</Text>,
			);
			remaining = remaining.slice(boldMatch[0].length);
			continue;
		}

		// Italic: *text*
		const italicMatch = remaining.match(/^\*([^*]+)\*/);
		if (italicMatch) {
			elements.push(
				<Text key={keyIdx++} italic>
					{italicMatch[1]}
				</Text>,
			);
			remaining = remaining.slice(italicMatch[0].length);
			continue;
		}

		// Regular character
		const nextSpecial = remaining.search(/[`*]/);
		if (nextSpecial === -1) {
			elements.push(<Text key={keyIdx++}>{remaining}</Text>);
			break;
		} else if (nextSpecial === 0) {
			// Not a valid markdown, just output the character
			elements.push(<Text key={keyIdx++}>{remaining[0]}</Text>);
			remaining = remaining.slice(1);
		} else {
			elements.push(<Text key={keyIdx++}>{remaining.slice(0, nextSpecial)}</Text>);
			remaining = remaining.slice(nextSpecial);
		}
	}

	return elements;
}

export default function ChapterView({
	chapter,
	currentIndex,
	totalChapters,
}: Props) {
	// Parse markdown content
	const renderContent = (content: string) => {
		const lines = content.split('\n');
		const elements: JSX.Element[] = [];
		let inCodeBlock = false;
		let codeLines: string[] = [];
		let codeLanguage = '';
		let lineIdx = 0;

		for (const line of lines) {
			// Code block start/end
			if (line.startsWith('```')) {
				if (!inCodeBlock) {
					inCodeBlock = true;
					codeLanguage = line.replace('```', '').trim();
					codeLines = [];
				} else {
					// Code block end - render the code block
					inCodeBlock = false;
					elements.push(
						<Box
							key={`code-${lineIdx}`}
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
				lineIdx++;
				continue;
			}

			if (inCodeBlock) {
				codeLines.push(line);
				lineIdx++;
				continue;
			}

			// Empty line
			if (!line.trim()) {
				elements.push(<Text key={lineIdx}> </Text>);
				lineIdx++;
				continue;
			}

			// Headers
			if (line.startsWith('### ')) {
				elements.push(
					<Box key={lineIdx} marginTop={1}>
						<Text bold color="cyan">
							{line.replace(/^###\s*/, '')}
						</Text>
					</Box>,
				);
			} else if (line.startsWith('## ')) {
				elements.push(
					<Box key={lineIdx} marginTop={1}>
						<Text bold color="cyan" underline>
							{line.replace(/^##\s*/, '')}
						</Text>
					</Box>,
				);
			} else if (line.startsWith('# ')) {
				elements.push(
					<Box key={lineIdx} marginTop={1}>
						<Text bold color="yellow">
							{line.replace(/^#\s*/, '')}
						</Text>
					</Box>,
				);
			} else if (line.match(/^\d+\.\s/)) {
				// Numbered list
				const content = line.replace(/^\d+\.\s*/, '');
				const number = line.match(/^(\d+)\./)?.[1] ?? '•';
				elements.push(
					<Box key={lineIdx} marginLeft={2}>
						<Text color="yellow">{number}. </Text>
						<Text>{renderInlineMarkdown(content)}</Text>
					</Box>,
				);
			} else if (line.startsWith('- ') || line.startsWith('* ')) {
				// Bullet list
				elements.push(
					<Box key={lineIdx} marginLeft={2}>
						<Text color="cyan">• </Text>
						<Text>{renderInlineMarkdown(line.replace(/^[-*]\s*/, ''))}</Text>
					</Box>,
				);
			} else if (line.startsWith('   ')) {
				// Indented content (sub-items)
				elements.push(
					<Box key={lineIdx} marginLeft={4}>
						<Text>{renderInlineMarkdown(line.trim())}</Text>
					</Box>,
				);
			} else {
				// Regular paragraph with inline markdown
				elements.push(
					<Box key={lineIdx}>
						<Text>{renderInlineMarkdown(line)}</Text>
					</Box>,
				);
			}
			lineIdx++;
		}

		return elements;
	};

	return (
		<Box flexDirection="column" paddingX={2}>
			{/* Chapter header */}
			<Box
				marginBottom={1}
				borderStyle="round"
				borderColor="cyan"
				paddingX={2}
				paddingY={1}
			>
				<Box flexDirection="column">
					<Box>
						<Text bold color="cyan">
							Chapter {chapter.id}: {chapter.title}
						</Text>
						<Text dimColor>  [{currentIndex + 1}/{totalChapters}]</Text>
					</Box>
					<Text dimColor italic>
						{chapter.summary}
					</Text>
				</Box>
			</Box>

			{/* Chapter content */}
			<Box flexDirection="column" paddingX={1}>
				{renderContent(chapter.content)}
			</Box>
		</Box>
	);
}

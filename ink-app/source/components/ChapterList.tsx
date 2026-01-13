/**
 * Chapter list component
 */

import React from 'react';
import {Box, Text} from 'ink';
import {type Tutorial} from '../types.js';

type Props = {
	tutorial: Tutorial;
	currentIndex: number;
};

export default function ChapterList({tutorial, currentIndex}: Props) {
	return (
		<Box flexDirection="column" paddingX={2} paddingY={1}>
			<Box marginBottom={1}>
				<Text bold color="cyan">
					{tutorial.title}
				</Text>
			</Box>

			<Box marginBottom={1}>
				<Text dimColor italic>
					{tutorial.description}
				</Text>
			</Box>

			<Box flexDirection="column" marginTop={1}>
				<Text bold>Chapters:</Text>
				{tutorial.chapters.map((chapter, idx) => {
					const isCurrent = idx === currentIndex;
					return (
						<Box key={chapter.id} marginLeft={2} marginY={0}>
							<Text color={isCurrent ? 'yellow' : 'white'} bold={isCurrent}>
								{isCurrent ? '▶ ' : '  '}
								{chapter.id}. {chapter.title}
							</Text>
							{isCurrent && <Text color="yellow"> ← You are here</Text>}
						</Box>
					);
				})}
			</Box>

			<Box marginTop={2}>
				<Text dimColor>
					Type <Text color="yellow">/goto [N]</Text> to jump to a chapter, or{' '}
					<Text color="yellow">/back</Text> to return
				</Text>
			</Box>
		</Box>
	);
}

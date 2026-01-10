/**
 * Welcome screen component
 */

import React from 'react';
import {Box, Text} from 'ink';
import BigText from 'ink-big-text';
import Gradient from 'ink-gradient';

export default function Welcome() {
	return (
		<Box flexDirection="column" padding={1}>
			<Gradient name="passion">
				<BigText text="Janett" font="chrome" />
			</Gradient>
			
			<Box marginTop={1} marginBottom={1}>
				<Text color="cyan" bold>
					Learn anything with AI-generated tutorials
				</Text>
			</Box>

			<Box flexDirection="column" marginTop={1}>
				<Text dimColor>Enter a topic to generate a comprehensive tutorial:</Text>
				<Text color="green">  • "Python basics"</Text>
				<Text color="green">  • "Photography for beginners"</Text>
				<Text color="green">  • "How to cook pasta"</Text>
			</Box>

			<Box marginTop={2}>
				<Text dimColor>Type your topic and press Enter to begin...</Text>
			</Box>
		</Box>
	);
}

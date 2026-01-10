/**
 * Loading indicator component
 */

import React from 'react';
import {Box, Text} from 'ink';
import Spinner from 'ink-spinner';

type Props = {
	message?: string;
};

export default function Loading({message = 'Loading...'}: Props) {
	return (
		<Box paddingX={2} paddingY={1}>
			<Text color="cyan">
				<Spinner type="dots" />
			</Text>
			<Text> {message}</Text>
		</Box>
	);
}

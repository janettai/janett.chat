/**
 * Input component - Clean, minimal prompt
 */

import React from 'react';
import {Box, Text} from 'ink';
import TextInput from 'ink-text-input';

type Props = {
	value: string;
	onChange: (value: string) => void;
	onSubmit: (value: string) => void;
	placeholder?: string;
};

export default function Input({
	value,
	onChange,
	onSubmit,
	placeholder = '',
}: Props) {
	return (
		<Box paddingX={2} paddingY={1}>
			<Text color="yellow" bold>❯ </Text>
			<TextInput
				value={value}
				onChange={onChange}
				onSubmit={onSubmit}
				placeholder={placeholder}
			/>
		</Box>
	);
}

import React from 'react';
import test from 'ava';
import {render} from 'ink-testing-library';
import Welcome from './source/components/Welcome.js';
import Help from './source/components/Help.js';
import Loading from './source/components/Loading.js';

test('Welcome component renders title', t => {
	const {lastFrame} = render(<Welcome />);
	const frame = lastFrame();

	t.true(frame?.includes('Janett') ?? false);
	t.true(frame?.includes('Learn anything') ?? false);
});

test('Help component shows tutorial commands', t => {
	const {lastFrame} = render(<Help mode="tutorial" />);
	const frame = lastFrame();

	t.true(frame?.includes('/next') ?? false);
	t.true(frame?.includes('/prev') ?? false);
	t.true(frame?.includes('/chapters') ?? false);
});

test('Help component shows chat commands', t => {
	const {lastFrame} = render(<Help mode="chat" />);
	const frame = lastFrame();

	t.true(frame?.includes('/back') ?? false);
	t.true(frame?.includes('/clear') ?? false);
});

test('Loading component shows message', t => {
	const {lastFrame} = render(<Loading message="Generating..." />);
	const frame = lastFrame();

	t.true(frame?.includes('Generating...') ?? false);
});

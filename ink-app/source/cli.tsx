#!/usr/bin/env node
import React from 'react';
import {render} from 'ink';
import meow from 'meow';
import dotenv from 'dotenv';
import App from './app.js';

// Load environment variables
dotenv.config();

meow(
	`
	Usage
	  $ janett

	Description
	  Learn anything with AI-generated tutorials, right in your terminal

	Commands
	  /next          - Go to next chapter
	  /prev          - Go to previous chapter
	  /chapters      - View all chapters
	  /goto [N]      - Jump to chapter N
	  /more          - Generate more chapters
	  /chat          - Switch to chat mode
	  /quit          - Exit Janett

	Examples
	  $ janett
	  > Python basics
	  
	  $ janett
	  > Photography for beginners
`,
	{
		importMeta: import.meta,
		flags: {},
	},
);

render(<App />);

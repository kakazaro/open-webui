import { browser, dev } from '$app/environment';
// import { version } from '../../package.json';

export const APP_NAME = 'Open WebUI';

export const WEBUI_HOSTNAME = browser ? (dev ? `${location.hostname}:8080` : ``) : '';
export const WEBUI_BASE_URL = browser ? (dev ? `http://${WEBUI_HOSTNAME}` : ``) : ``;
export const WEBUI_API_BASE_URL = `${WEBUI_BASE_URL}/api/v1`;

export const OLLAMA_API_BASE_URL = `${WEBUI_BASE_URL}/ollama`;
export const OPENAI_API_BASE_URL = `${WEBUI_BASE_URL}/openai`;
export const AUDIO_API_BASE_URL = `${WEBUI_BASE_URL}/api/v1/audio`;
export const IMAGES_API_BASE_URL = `${WEBUI_BASE_URL}/api/v1/images`;
export const RETRIEVAL_API_BASE_URL = `${WEBUI_BASE_URL}/api/v1/retrieval`;

export const WEBUI_VERSION = APP_VERSION;
export const WEBUI_BUILD_HASH = APP_BUILD_HASH;
export const REQUIRED_OLLAMA_VERSION = '0.1.16';

export const SUPPORTED_FILE_TYPE = [
	'application/epub+zip',
	'application/pdf',
	'text/plain',
	'text/csv',
	'text/xml',
	'text/html',
	'text/x-python',
	'text/css',
	'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	'application/octet-stream',
	'application/x-javascript',
	'text/markdown',
	'audio/mpeg',
	'audio/wav',
	'audio/ogg',
	'audio/x-m4a'
];

export const SUPPORTED_FILE_EXTENSIONS = [
	'md',
	'rst',
	'go',
	'py',
	'java',
	'sh',
	'bat',
	'ps1',
	'cmd',
	'js',
	'ts',
	'css',
	'cpp',
	'hpp',
	'h',
	'c',
	'cs',
	'htm',
	'html',
	'sql',
	'log',
	'ini',
	'pl',
	'pm',
	'r',
	'dart',
	'dockerfile',
	'env',
	'php',
	'hs',
	'hsc',
	'lua',
	'nginxconf',
	'conf',
	'm',
	'mm',
	'plsql',
	'perl',
	'rb',
	'rs',
	'db2',
	'scala',
	'bash',
	'swift',
	'vue',
	'svelte',
	'doc',
	'docx',
	'pdf',
	'csv',
	'txt',
	'xls',
	'xlsx',
	'pptx',
	'ppt',
	'msg'
];

export const PASTED_TEXT_CHARACTER_LIMIT = 1000;

// Source: https://kit.svelte.dev/docs/modules#$env-static-public
// This feature, akin to $env/static/private, exclusively incorporates environment variables
// that are prefixed with config.kit.env.publicPrefix (usually set to PUBLIC_).
// Consequently, these variables can be securely exposed to client-side code.

// TODO: renesas
export const CODING_COMMANDS = [
	{
		value: 'code_review',
		title: 'Code Review',
		replace:
			'Please review the code (Consider: 1. Code quality and adherence to best practices 2. Potential bugs or edge cases 3. Performance optimizations 4. Readability and maintainability 5. Any security concerns Suggest improvements and explain your reasoning for each suggestion.)'
	},
	{
		value: 'code_refactor',
		title: 'Code Refactor',
		replace: 'please go through the following thought process to refactor it according to coding guidelines: 1. Analyze the current structure and identify areas for improvement. 2. Consider best practices in code organization, readability, and efficiency. 3. Gather relevant coding standards or conventions that apply. 4. After this analysis, present the refactored code snippet and a brief summary of the improvements made. Refactor the code snippet above according to the guidelines and provide: - The optimized code snippet only. - A few bullet points highlighting the changes and improvements made.'
	},
	{
		value: 'code_explain',
		title: 'Code Explain',
		replace: 'Provide a detailed explanation of the code snippet. Begin with a concise overview of its main purpose, then generate a series of reasoning steps that break down each statement. For each statement, clarify its function, expected outcome, and any external information or context needed to understand it fully. If necessary, suggest actions to explore related details or examples that could enhance comprehension.'
	},
	{
		value: 'code_generation_C',
		title: 'Code generation (C/C++)',
		replace: 'Provide a detailed explanation of the code snippet. Begin with a concise overview of its main purpose, then generate a series of reasoning steps that break down each statement. For each statement, clarify its function, expected outcome, and any external information or context needed to understand it fully. If necessary, suggest actions to explore related details or examples that could enhance comprehension.'
	},
	{
		value: 'code_generation_Py',
		title: 'Code generation (Python)',
		replace: 'Create Python code to realize the description below. Please include enough comments and error handling.'
	},
	{
		value: 'unit_test_generation',
		title: 'Unit test generation',
		replace: 'Write a comprehensive set of unit tests for the selected code. It should setup, run tests that check for correctness including important edge cases, and teardown. Ensure that the tests are complete and sophisticated. Give the tests just as chat output.'
	}
];

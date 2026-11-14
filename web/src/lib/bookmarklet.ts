import source from '../../../dupr/bookmarklet.js?raw';

/** Turn dupr/bookmarklet.js into a one-line javascript: URL that sends the data back to `target`. */
export function bookmarkletHref(target: string): string {
	const code = source
		.split('\n')
		.map((l) => l.trim())
		.filter((l) => l && !l.startsWith('//'))
		.join(' ')
		.replace('__TARGET__', target)
		.replace(/\s+/g, ' ');
	return 'javascript:' + encodeURIComponent(code);
}

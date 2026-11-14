// The last sync is kept in this browser only (localStorage), so the report can be reopened later.
const STORE_KEY = 'dupr-analysis:last-sync';

export type LastSync = { payload: string; at: number };

export const lastSyncStore = {
	get(): LastSync | null {
		try {
			return JSON.parse(localStorage.getItem(STORE_KEY) ?? 'null');
		} catch {
			return null;
		}
	},
	set(v: LastSync) {
		try {
			localStorage.setItem(STORE_KEY, JSON.stringify(v));
		} catch {
			/* storage full or blocked */
		}
	},
	clear() {
		try {
			localStorage.removeItem(STORE_KEY);
		} catch {
			/* storage blocked */
		}
	}
};

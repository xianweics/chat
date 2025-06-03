export const authInitialState = {
    user: null,
    token: null,
    status: 'idle', // idle, loading, succeeded, failed
    error: null
};

export const chatInitialState = {
    sessions: {},
    activeSessionId: null,
    status: 'idle', // idle, loading, succeeded, failed
    error: null
};
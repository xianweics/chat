import api from '@api';

export const loadSessions = () => async (dispatch, getState) => {
    dispatch({type: 'chat/loadSessionsRequest'});
    try {
        const token = getState().auth.token;
        const response = await api.get('/api/sessions', {
            headers: {Authorization: `Bearer ${token}`}
        });
        dispatch({type: 'chat/loadSessionsSuccess', payload: response.data});
        return {success: true};
    } catch (error) {
        const errorMessage = error.response?.data?.error || 'Failed to load sessions';
        dispatch({type: 'chat/loadSessionsFailure', payload: errorMessage});
        return {success: false, error: errorMessage};
    }
};

export const createSession = () => async (dispatch, getState) => {
    dispatch({type: 'chat/createSessionRequest'});
    try {
        const token = getState().auth.token;
        const response = await api.post('/api/sessions', {}, {
            headers: {Authorization: `Bearer ${token}`}
        });
        dispatch({type: 'chat/createSessionSuccess', payload: response.data});
        return {success: true, sessionId: response.data.id};
    } catch (error) {
        const errorMessage = error.response?.data?.error || 'Failed to create session';
        dispatch({type: 'chat/createSessionFailure', payload: errorMessage});
        return {success: false, error: errorMessage};
    }
};

export const loadMessages = (sessionId) => async (dispatch, getState) => {
    dispatch({type: 'chat/loadMessagesRequest'});
    try {
        const token = getState().auth.token;
        const response = await api.get(`/api/sessions/${sessionId}/messages`, {
            headers: {Authorization: `Bearer ${token}`}
        });
        dispatch({
            type: 'chat/loadMessagesSuccess',
            payload: {sessionId, messages: response.data}
        });
        return {success: true};
    } catch (error) {
        const errorMessage = error.response?.data?.error || 'Failed to load messages';
        dispatch({type: 'chat/loadMessagesFailure', payload: errorMessage});
        return {success: false, error: errorMessage};
    }
};

export const sendMessage = (sessionId, content) => async (dispatch, getState) => {
    dispatch({type: 'chat/sendMessageRequest'});
    try {
        const token = getState().auth.token;
        const response = await api.post('/api/chat', {
            sessionId, content
        }, {
            headers: {Authorization: `Bearer ${token}`}
        });

        const {userMsg, aiMsg} = response.data;

        dispatch({
            type: 'chat/sendMessageSuccess',
            payload: {sessionId, userMessage: userMsg, aiMessage: aiMsg}
        });

        return {success: true};
    } catch (error) {
        const errorMessage = error.response?.data?.error || 'Failed to send message';
        dispatch({type: 'chat/sendMessageFailure', payload: errorMessage});
        return {success: false, error: errorMessage};
    }
};

export const setActiveSession = (sessionId) => (dispatch) => {
    dispatch({type: 'chat/setActiveSession', payload: sessionId});
};
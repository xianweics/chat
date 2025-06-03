import {chatInitialState} from "@src/store/config";

const chat = (state = chatInitialState, action) => {
    switch (action.type) {
        case 'chat/loadSessionsRequest':
            return {...state, status: 'loading'};
        case 'chat/loadSessionsSuccess':
            return {
                ...state,
                status: 'succeeded',
                sessions: action.payload.reduce((acc, session) => {
                    acc[session.id] = {
                        ...session,
                        messages: session.Messages ? [session.Messages[0]] : [] // Only last message
                    };
                    return acc;
                }, {})
            };
        case 'chat/loadSessionsFailure':
            return {...state, status: 'failed', error: action.payload};
        case 'chat/createSessionRequest':
            return {...state, status: 'loading'};
        case 'chat/createSessionSuccess':
            return {
                ...state,
                status: 'succeeded',
                activeSessionId: action.payload.id,
                sessions: {
                    ...state.sessions,
                    [action.payload.id]: {
                        id: action.payload.id,
                        title: action.payload.title,
                        messages: []
                    }
                }
            };
        case 'chat/createSessionFailure':
            return {...state, status: 'failed', error: action.payload};
        case 'chat/loadMessagesRequest':
            return {...state, status: 'loading'};
        case 'chat/loadMessagesSuccess':
            return {
                ...state,
                status: 'succeeded',
                sessions: {
                    ...state.sessions,
                    [action.payload.sessionId]: {
                        ...state.sessions[action.payload.sessionId],
                        messages: action.payload.messages
                    }
                },
                activeSessionId: action.payload.sessionId
            };
        case 'chat/loadMessagesFailure':
            return {...state, status: 'failed', error: action.payload};
        case 'chat/sendMessageRequest':
            return {...state, status: 'loading'};
        case 'chat/sendMessageSuccess':
            const {sessionId, userMessage, aiMessage} = action.payload;
            return {
                ...state,
                status: 'succeeded',
                sessions: {
                    ...state.sessions,
                    [sessionId]: {
                        ...state.sessions[sessionId],
                        messages: [
                            ...state.sessions[sessionId].messages,
                            userMessage,
                            aiMessage
                        ]
                    }
                }
            };
        case 'chat/setActiveSession':
            return {...state, activeSessionId: action.payload};
        default:
            return state;
    }
}

export default chat;
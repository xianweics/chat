import {AUTH_STATUS_LOADING, CHAT_STATUS_FAILED, CHAT_STATUS_LOADING, CHAT_STATUS_SUCCEEDED, CHAT_STATUS_IDLE} from "@src/config";
import {modules, MODULE_NAME} from "@store/config";
import * as actionTypes from "./actionTypes";

const initialState = {
  sessions: {},
  activeSessionId: null,
  status: CHAT_STATUS_IDLE, // idle, loading, succeeded, failed
  error: null,
  [MODULE_NAME]: modules.chat
};

const chat = (state = initialState, action) => {
  const {type, payload} = action;
  const {id, title, sessionId: payloadSessionId, messages} = payload || {};
  switch (type) {
    case actionTypes.LOAD_SESSION_REQUEST:
      return {...state, status: AUTH_STATUS_LOADING};
    case actionTypes.LOAD_SESSION_SUCCESS:
      return {
        ...state,
        status: CHAT_STATUS_SUCCEEDED,
        sessions: payload.reduce((acc, session) => {
          acc[session.id] = {
            ...session,
            messages: session.Messages ? [session.Messages[0]] : [] // Only last message
          };
          return acc;
        }, {})
      };
    case actionTypes.LOAD_SESSION_FAILURE:
      return {...state, status: CHAT_STATUS_FAILED, error: payload};
    case actionTypes.CREATE_SESSION_REQUEST:
      return {...state, status: CHAT_STATUS_LOADING};
    case actionTypes.CREATE_SESSION_SUCCESS:
      return {
        ...state,
        status: CHAT_STATUS_SUCCEEDED,
        activeSessionId: id,
        sessions: {
          ...state.sessions,
          [id]: {
            id,
            title,
            messages: []
          }
        }
      };
    case actionTypes.CREATE_SESSION_FAILURE:
      return {...state, status: CHAT_STATUS_FAILED, error: payload};
    case actionTypes.LOAD_MESSAGE_REQUEST:
      return {...state, status: CHAT_STATUS_LOADING};
    case actionTypes.LOAD_MESSAGE_SUCCESS:
      return {
        ...state,
        status: CHAT_STATUS_SUCCEEDED,
        sessions: {
          ...state.sessions,
          [payloadSessionId]: {
            ...state.sessions[payloadSessionId],
            messages
          }
        },
        activeSessionId: payloadSessionId
      };
    case actionTypes.SEND_MESSAGE_FAILURE:
      return {...state, status: CHAT_STATUS_FAILED, error: payload};
    case actionTypes.SEND_MESSAGE_REQUEST:
      return {...state, status: CHAT_STATUS_LOADING};
    case actionTypes.SEND_MESSAGE_SUCCESS:
      const {sessionId, userMessage, aiMessage} = payload;
      return {
        ...state,
        status: CHAT_STATUS_SUCCEEDED,
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
    case actionTypes.SET_ACTIVE_SESSION:
      return {...state, activeSessionId: payload};
    default:
      return state;
  }
}

export default chat;
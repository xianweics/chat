import * as statuses from './statuses.config';
import {MODULE_NAME, modules} from '@store/config';
import * as actionTypes from './actionTypes';

const initialState = {
  sessions: {
    status: statuses.SESSION_STATUS_IDLE,
    error: null,
    sessions: {},
  },
  messages: {
    error: null,
    messages: [],
    status: statuses.MESSAGE_STATUS_IDLE,
  },
  create: {
    error: null,
    status: statuses.CREATE_STATUS_IDLE,
  },
  send: {
    error: null,
    status: statuses.SEND_STATUS_IDLE,
  },
  activeSessionId: null,
  [MODULE_NAME]: modules.chat,
};

const chat = (state = initialState, action) => {
  const {type, payload} = action;
  const {id, title, sessionId: payloadSessionId, messages} = payload || {};
  switch (type) {
    case actionTypes.LOAD_SESSION_REQUEST:
      return {
        ...state,
        sessions: {
          sessions: {},
          status: statuses.SESSION_STATUS_LOADING,
          error: null,
        },
      };
    case actionTypes.LOAD_SESSION_SUCCESS:
      return {
        ...state,
        sessions: {
          error: null,
          status: statuses.SESSION_STATUS_SUCCEEDED,
          sessions: payload.reduce((acc, session) => {
            acc[session.id] = session;
            return acc;
          }, {}),
        },
      };
    case actionTypes.LOAD_SESSION_FAILURE:
      return {
        ...state,
        sessions: {
          sessions: {},
          status: statuses.SESSION_STATUS_FAILED,
          error: payload,
        },
      };
    case actionTypes.CREATE_SESSION_REQUEST:
      return {
        ...state,
        create: {
          error: null,
          status: statuses.CREATE_STATUS_LOADING,
        },
      };
    case actionTypes.CREATE_SESSION_FAILURE:
      return {
        ...state,
        create: {
          error: payload,
          status: statuses.CREATE_STATUS_FAILED,
        },
      };
    case actionTypes.CREATE_SESSION_SUCCESS:
      return {
        ...state,
        activeSessionId: id,
        create: {
          status: statuses.CREATE_STATUS_SUCCEEDED,
          error: null,
        },
        sessions: {
          ...state.sessions,
          sessions: {
            ...state.sessions.sessions,
            [id]: {
              id,
              title,
              messages: [],
            },
          }
        }
      };
    case actionTypes.LOAD_MESSAGE_REQUEST:
      return {
        ...state,
        messages: {
          status: statuses.MESSAGE_STATUS_LOADING,
          error: null,
          messages: [],
        },
      };
    case actionTypes.LOAD_MESSAGE_RESET:
      return {
        ...state,
        messages: {
          status: statuses.MESSAGE_STATUS_IDLE,
          error: null,
          messages: [],
        },
      };
    case actionTypes.LOAD_MESSAGE_SUCCESS:
      return {
        ...state,
        messages: {
          status: statuses.MESSAGE_STATUS_SUCCEEDED,
          error: null,
          messages,
        },
        create: {
          ...state.create,
          activeSessionId: payloadSessionId,
        },
      };
    case actionTypes.LOAD_MESSAGE_FAILURE:
      return {
        ...state,
        messages: {
          status: statuses.MESSAGE_STATUS_FAILED,
          error: payload,
          messages: [],
        },
      };
    case actionTypes.SEND_MESSAGE_REQUEST:
      return {
        ...state,
        send: {
          status: statuses.SEND_STATUS_LOADING,
          error: null,
        },
      };
    case actionTypes.SEND_MESSAGE_FAILURE:
      return {
        ...state,
        send: {
          status: statuses.SEND_STATUS_FAILED,
          error: payload,
        },
      };
    case actionTypes.SEND_MESSAGE_SUCCESS:
      const {userMessage, aiMessage, sessionId} = payload;
      const normalUpdatedData = {
        ...state,
        messages: {
          status: statuses.MESSAGE_STATUS_SUCCEEDED,
          error: null,
          messages: [
            ...state.messages.messages,
            userMessage,
            aiMessage,
          ],
        },
        send: {
          status: statuses.SEND_STATUS_SUCCEEDED,
          error: null,
        },
      };
      if (state.sessions.sessions[sessionId].messages.length === 0) {
        normalUpdatedData.sessions = {
          ...state.sessions,
          sessions: {
            ...state.sessions.sessions,
            [sessionId]: {
              ...state.sessions.sessions[sessionId],
              messages: [userMessage],
            },
          }
        }
      }
      return normalUpdatedData;
    case actionTypes.SET_ACTIVE_SESSION:
      return {...state, activeSessionId: payload};
    default:
      return state;
  }
}

export default chat;
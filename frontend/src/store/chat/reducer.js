import * as statuses from './statuses.config';
import {MODULE_NAME, modules} from '@store/config';
import * as actionTypes from './actionTypes';

const initialState = {
  sessions: {
    status: statuses.SESSION_STATUS_IDLE,
    error: null,
    data: {},
  },
  messages: {
    error: null,
    data: [],
    status: statuses.LOAD_MESSAGES_STATUS_IDLE,
  },
  create: {
    error: null,
    status: statuses.CREATE_SESSION_STATUS_IDLE,
  },
  send: {
    error: null,
    status: statuses.SEND_MESSAGE_STATUS_IDLE,
  },
  activeSessionId: null,
  [MODULE_NAME]: modules.chat,
};

const chat = (state = initialState, action) => {
  const {type, payload} = action;
  const {sessionId, data} = payload || {};
  switch (type) {
    case actionTypes.LOAD_SESSIONS_REQUEST:
      return {
        ...state,
        sessions: {
          data: {},
          status: statuses.SESSION_STATUS_LOADING,
          error: null,
        },
      };
    case actionTypes.LOAD_SESSIONS_SUCCESS:
      return {
        ...state,
        sessions: {
          error: null,
          status: statuses.SESSION_STATUS_SUCCEEDED,
          data: payload.reduce((acc, session) => {
            acc[session.id] = session;
            return acc;
          }, {}),
        },
      };
    case actionTypes.LOAD_SESSIONS_FAILURE:
      return {
        ...state,
        sessions: {
          data: {},
          status: statuses.SESSION_STATUS_FAILED,
          error: payload,
        },
      };
    case actionTypes.CREATE_SESSIONS_REQUEST:
      return {
        ...state,
        create: {
          error: null,
          status: statuses.CREATE_SESSION_STATUS_LOADING,
        },
      };
    case actionTypes.CREATE_SESSIONS_FAILURE:
      return {
        ...state,
        create: {
          error: payload,
          status: statuses.CREATE_SESSION_STATUS_FAILED,
        },
      };
    case actionTypes.CREATE_SESSIONS_SUCCESS:
      const {id} = payload;
      return {
        ...state,
        activeSessionId: id,
        create: {
          status: statuses.CREATE_SESSION_STATUS_SUCCEEDED,
          error: null,
        },
        sessions: {
          ...state.sessions,
          data: {
            ...state.sessions.data,
            [id]: {
              ...payload,
              messages: [],
            },
          },
        },
      };
    case actionTypes.LOAD_MESSAGES_REQUEST:
      return {
        ...state,
        messages: {
          status: statuses.LOAD_MESSAGES_STATUS_LOADING,
          error: null,
          data: [],
        },
      };
    case actionTypes.LOAD_MESSAGES_SUCCESS:
      return {
        ...state,
        messages: {
          status: statuses.LOAD_MESSAGES_STATUS_SUCCEEDED,
          error: null,
          data,
        },
        create: {
          ...state.create,
          activeSessionId: sessionId,
        },
      };
    case actionTypes.LOAD_MESSAGES_FAILURE:
      return {
        ...state,
        messages: {
          status: statuses.LOAD_MESSAGES_STATUS_FAILED,
          error: payload,
          data: [],
        },
      };
    case actionTypes.SEND_MESSAGE_REQUEST:
      return {
        ...state,
        send: {
          status: statuses.SEND_MESSAGE_STATUS_LOADING,
          error: null,
        },
      };
    case actionTypes.UPDATE_TEMP_MESSAGES:
      const updateType = payload.type;
      if (updateType === 'remove') {
        return {
          ...state,
          messages: {
            ...state.messages,
            data: state.messages.data.filter(({id}) => !data.includes(id)),
          },
        };
      } else {
        return {
          ...state,
          messages: {
            ...state.messages,
            data: [
              ...state.messages.data,
              ...data,
            ],
          },
        };
      }

    case actionTypes.SEND_MESSAGES_FAILURE:
      return {
        ...state,
        send: {
          status: statuses.SEND_MESSAGE_STATUS_FAILED,
          error: payload,
        },
      };
    case actionTypes.SEND_MESSAGE_SUCCESS:
      const {removeData} = payload;
      const normalUpdatedData = {
        ...state,
        messages: {
          status: statuses.LOAD_MESSAGES_STATUS_SUCCEEDED,
          error: null,
          data: [
            ...state.messages.data.filter(({id}) => !removeData.includes(id)),
            data,
          ],
        },
        send: {
          status: statuses.SEND_MESSAGE_STATUS_SUCCEEDED,
          error: null,
        },
      };
      if (state.sessions.data[sessionId].messages.length === 0) {
        normalUpdatedData.sessions = {
          ...state.sessions,
          data: {
            ...state.sessions.data,
            [sessionId]: {
              ...state.sessions.data[sessionId],
              messages: [
                ...state.sessions.data[sessionId].messages,
                data,
              ],
            },
          },
        };
      }
      return normalUpdatedData;
    case actionTypes.SET_ACTIVE_SESSION:
      return {...state, activeSessionId: payload};
    default:
      return state;
  }
};

export default chat;
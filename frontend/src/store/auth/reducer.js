import {authInitialState} from "@src/store/config";

const auth = (state = authInitialState, action) => {
    switch (action.type) {
        case 'auth/loginRequest':
            return {...state, status: 'loading'};
        case 'auth/loginSuccess':
            return {
                ...state,
                status: 'succeeded',
                user: action.payload.user,
                token: action.payload.token,
                error: null
            };
        case 'auth/loginFailure':
            return {...state, status: 'failed', error: action.payload};
        case 'auth/registerRequest':
            return {...state, status: 'loading'};
        case 'auth/registerSuccess':
            return {...state, status: 'succeeded', error: null};
        case 'auth/registerFailure':
            return {...state, status: 'failed', error: action.payload};
        case 'auth/logout':
            return {...authInitialState};
        default:
            return state;
    }
}

export default auth;

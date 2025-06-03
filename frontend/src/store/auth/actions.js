import api from '@api';

export const registerUser = (username, password) => async (dispatch) => {
    dispatch({type: 'auth/registerRequest'});
    try {
        await api.post('/api/register', {username, password});
        dispatch({type: 'auth/registerSuccess'});
        return {success: true};
    } catch (error) {
        const errorMessage = error.response?.data?.error || 'Registration failed';
        dispatch({type: 'auth/registerFailure', payload: errorMessage});
        return {success: false, error: errorMessage};
    }
};

export const loginUser = (username, password) => async (dispatch) => {
    dispatch({type: 'auth/loginRequest'});
    try {
        const response = await api.post('/api/login', {username, password});
        const {token} = response.data;
        localStorage.setItem('token', token);

        // 解析JWT获取用户信息
        const payload = JSON.parse(atob(token.split('.')[1]));
        const user = {id: payload.userId, username: payload.username};

        dispatch({type: 'auth/loginSuccess', payload: {user, token}});
        return {success: true, user};
    } catch (error) {
        const errorMessage = error.response?.data?.error || 'Login failed';
        dispatch({type: 'auth/loginFailure', payload: errorMessage});
        return {success: false, error: errorMessage};
    }
};

export const logoutUser = () => (dispatch) => {
    localStorage.removeItem('token');
    dispatch({type: 'auth/logout'});
    dispatch({type: 'chat/setActiveSession', payload: null});
};
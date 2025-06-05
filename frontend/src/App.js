import {useAuth} from './hooks/useAuth';
import Main from "@components/Main";
import {useEffect} from "react";
import {TOKEN} from "@src/config";
import {parseToken} from "@src/utils";
import {LOGIN_SUCCESS} from "@store/auth/actionTypes";
import {loadSessions} from "@store/chat/actions";
import {useDispatch} from "react-redux";
import AuthForm from "@components/AuthForm";

const App = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    const token = localStorage.getItem(TOKEN);
    if (token) {
      try {
        const {userId, username} = parseToken(token);
        dispatch({
          type: LOGIN_SUCCESS,
          payload: {user: {id: userId, username}, token}
        });
        dispatch(loadSessions());
      } catch (e) {
        localStorage.removeItem(TOKEN);
        console.error(e);
      }
    }
  }, [dispatch]);

  const {isAuthenticated} = useAuth();
  return isAuthenticated ? <Main/> : <AuthForm/>;
}

export default App;
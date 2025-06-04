import {useMemo} from 'react';
import {useSelector} from 'react-redux';
import {AUTH_STATUS_LOADING} from "@src/config";
import {modules} from "@store/config";

export const useAuth = () => {
  const {user, token, status} = useSelector(state => state[modules.auth]);
  const isAuthenticated = useMemo(() => !!(user && token), [user, token]);

  return {
    isAuthenticated,
    isLoading: status === AUTH_STATUS_LOADING
  };
}; 
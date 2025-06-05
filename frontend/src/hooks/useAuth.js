import {useMemo} from 'react';
import {useSelector} from 'react-redux';
import {modules} from '@store/config';

export const useAuth = () => {
  const {user, token} = useSelector(state => state[modules.auth]);
  const isAuthenticated = useMemo(() => !!(user && token), [user, token]);

  return {
    isAuthenticated
  };
}; 
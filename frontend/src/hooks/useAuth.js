import {useMemo} from 'react';
import {useSelector} from 'react-redux';
import {modules} from '@store/config';

export const useAuth = () => {
  const {user, token} = useSelector(state => state[modules.auth]);
  return useMemo(() => !!(user && token), [user, token]);
}; 
import {Spin} from 'antd';

import AuthForm from '../components/AuthForm';
import {useAuth} from '../hooks/useAuth';

const Login = () => {
  const {isLoading, isAuthenticated} = useAuth();
  if (isLoading) {
    return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>
      <Spin size="large"/>
    </div>;
  }
  if (!isAuthenticated) {
    return <AuthForm/>;
  }

  return null;
};

export default Login;







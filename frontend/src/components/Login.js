import AuthForm from '../components/AuthForm';
import {useAuth} from '../hooks/useAuth';

const Login = () => {
  const {isAuthenticated} = useAuth();
  
  return isAuthenticated ? null : <AuthForm/>;
};

export default Login;







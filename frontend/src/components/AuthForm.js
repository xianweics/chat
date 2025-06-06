import {useCallback, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Card, Form, Input, Typography} from 'antd';
import {LockOutlined, UserOutlined} from '@ant-design/icons';

import {loginUser, registerUser, resetUser} from '@store/auth/actions';
import {AUTH_STATUS_LOADING} from '@store/auth/statuses.config';
import {modules} from '@store/config';
import {loadSessions} from '@store/chat/actions';

const {Title} = Typography;

const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [form] = Form.useForm();
  const dispatch = useDispatch();
  const {status, error} = useSelector(state => state[modules.auth]);
  const handleSubmit = useCallback(async () => {
    const values = await form.validateFields();
    const {username, password} = values;
    const {success} = await dispatch(
        isLogin ? loginUser(username, password) : registerUser(username,
            password));
    if (success) {
      form.resetFields();
    }
    success && isLogin && dispatch(loadSessions());
  }, [dispatch, isLogin, form]);
  const toggleLogin = useCallback(() => {
    dispatch(resetUser());
    setIsLogin(!isLogin);
    form.resetFields();
  }, [isLogin, dispatch, form]);

  return (
      <Card style={{maxWidth: 400, margin: '50px auto'}}>
        <Title level={3} style={{textAlign: 'center', marginBottom: 30}}>
          {isLogin ? 'Login' : 'Register'}
        </Title>

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
              name="username"
              rules={[{required: true, message: 'Please enter username'}]}
          >
            <Input prefix={<UserOutlined/>} placeholder="Username"/>
          </Form.Item>

          <Form.Item
              name="password"
              rules={[{required: true, message: 'Please enter password'}]}
          >
            <Input.Password prefix={<LockOutlined/>} placeholder="Password"/>
          </Form.Item>

          {!isLogin && (
              <Form.Item
                  name="confirmPassword"
                  dependencies={['password']}
                  rules={[
                    {required: true, message: 'Please confirm password'},
                    ({getFieldValue}) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject('Passwords do not match');
                      },
                    }),
                  ]}
              >
                <Input.Password prefix={<LockOutlined/>}
                                placeholder="Confirm Password"/>
              </Form.Item>
          )}

          {error && (
              <div
                  style={{color: 'red', marginBottom: 15, textAlign: 'center'}}>
                {error === 'INVALID_CREDENTIALS'
                    ? 'Invalid username or password'
                    : error}
              </div>
          )}

          <Form.Item>
            <Button
                type="primary"
                htmlType="submit"
                block
                loading={status === AUTH_STATUS_LOADING}
            >
              {isLogin ? 'Login' : 'Register'}
            </Button>
          </Form.Item>
        </Form>

        <div style={{textAlign: 'center', marginTop: 15}}>
          <Button type="link" onClick={toggleLogin}>
            {isLogin ?
                'No account? Register now' :
                'Have an account? Login now'}
          </Button>
        </div>
      </Card>
  );
};

export default AuthForm;
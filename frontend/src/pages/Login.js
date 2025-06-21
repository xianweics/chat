import React, {useCallback} from 'react';
import {Button, Card, Form, Input, message, Typography} from 'antd';
import {useNavigate} from 'react-router-dom';
import {useDispatch, useSelector} from 'react-redux';
import {loginUser} from '@store/auth/actions';
import {LockOutlined, UserOutlined} from '@ant-design/icons';
import {modules} from '@store/config';
import {LOGIN_STATUS_LOADING} from '@store/auth/statuses.config';

const {Title} = Typography;

const Login = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [form] = Form.useForm();
  const {login} = useSelector(state => state[modules.auth]);

  const handleSubmit = useCallback(async () => {
    const values = await form.validateFields();
    const {username, password} = values;
    const {success} = await dispatch(loginUser(username, password));
    if (success) {
      message.success('Login successfully');
      navigate('/chat', {replace: true});
    } else {
      message.error('Login failed');
    }
  }, [dispatch, form, navigate]);

  const toRegister = useCallback(() => {
    navigate('/register');
  }, [navigate]);

  return (
      <Card style={{width: 400}}>
        <Title level={3} style={{textAlign: 'center', marginBottom: 30}}>
          Login
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

          <Form.Item>
            <Button
                type="primary"
                htmlType="submit"
                block
                loading={login.status === LOGIN_STATUS_LOADING}
            >
              Login
            </Button>
          </Form.Item>
        </Form>

        <div style={{textAlign: 'center', marginTop: 15}}>
          <Button type="link" onClick={toRegister}>
            No account? Register now
          </Button>
        </div>
      </Card>
  );
};

export default Login; 
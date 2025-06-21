import React, {useCallback} from 'react';
import {Button, Card, Form, Input, message, Typography} from 'antd';
import {useNavigate} from 'react-router-dom';
import {REGISTER_STATUS_LOADING} from '@store/auth/statuses.config';
import {registerUser} from '@store/auth/actions';
import {useDispatch, useSelector} from 'react-redux';
import {LockOutlined, UserOutlined} from '@ant-design/icons';
import {modules} from '@store/config';

const {Title} = Typography;

const Register = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [form] = Form.useForm();
  const {register} = useSelector(state => state[modules.auth]);
  const handleSubmit = useCallback(async () => {
    const values = await form.validateFields();
    const {username, password} = values;
    const {success} = await dispatch(registerUser(username,
        password));
    if (success) {
      message.success('Register successfully');
      form.resetFields();
    } else {
      message.error('Register failed');
    }
  }, [dispatch, form]);

  const toLogin = useCallback(() => {
    navigate('/login');
  }, [navigate]);

  return (
      <Card style={{width: 400}}>
        <Title level={3} style={{textAlign: 'center', marginBottom: 30}}>
          Register
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

          <Form.Item>
            <Button
                type="primary"
                htmlType="submit"
                block
                loading={register.status === REGISTER_STATUS_LOADING}
            >
              Register
            </Button>
          </Form.Item>
        </Form>

        <div style={{textAlign: 'center', marginTop: 15}}>
          <Button type="link" onClick={toLogin}>
            Have an account? Login now
          </Button>
        </div>
      </Card>
  );
};

export default Register; 
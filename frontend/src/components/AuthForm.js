import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Form, Input, Card, Typography} from 'antd';

import {UserOutlined, LockOutlined} from '@ant-design/icons';
import {registerUser, loginUser} from '@store/auth/actions';

const {Title} = Typography;

const AuthForm = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [form] = Form.useForm();
    const dispatch = useDispatch();
    const {status, error} = useSelector(state => state.auth);

    const handleSubmit = async () => {
        const values = await form.validateFields();

        if (isLogin) {
            dispatch(loginUser(values.username, values.password));
        } else {
            dispatch(registerUser(values.username, values.password));
        }
    };

    return (
        <Card style={{maxWidth: 400, margin: '50px auto'}}>
            <Title level={3} style={{textAlign: 'center', marginBottom: 30}}>
                {isLogin ? '登录' : '注册'}
            </Title>

            <Form form={form} layout="vertical" onFinish={handleSubmit}>
                <Form.Item
                    name="username"
                    rules={[{required: true, message: '请输入用户名'}]}
                >
                    <Input prefix={<UserOutlined/>} placeholder="用户名"/>
                </Form.Item>

                <Form.Item
                    name="password"
                    rules={[{required: true, message: '请输入密码'}]}
                >
                    <Input.Password prefix={<LockOutlined/>} placeholder="密码"/>
                </Form.Item>

                {!isLogin && (
                    <Form.Item
                        name="confirmPassword"
                        dependencies={['password']}
                        rules={[
                            {required: true, message: '请确认密码'},
                            ({getFieldValue}) => ({
                                validator(_, value) {
                                    if (!value || getFieldValue('password') === value) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject('两次输入的密码不一致');
                                },
                            }),
                        ]}
                    >
                        <Input.Password prefix={<LockOutlined/>} placeholder="确认密码"/>
                    </Form.Item>
                )}

                {error && (
                    <div style={{color: 'red', marginBottom: 15, textAlign: 'center'}}>
                        {error === 'INVALID_CREDENTIALS' ? '用户名或密码错误' : error}
                    </div>
                )}

                <Form.Item>
                    <Button
                        type="primary"
                        htmlType="submit"
                        block
                        loading={status === 'loading'}
                    >
                        {isLogin ? '登录' : '注册'}
                    </Button>
                </Form.Item>
            </Form>

            <div style={{textAlign: 'center', marginTop: 15}}>
                <Button type="link" onClick={() => setIsLogin(!isLogin)}>
                    {isLogin ? '没有账号？立即注册' : '已有账号？立即登录'}
                </Button>
            </div>
        </Card>
    );
};

export default AuthForm;
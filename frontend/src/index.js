import ReactDOM from 'react-dom/client';
import {Provider} from 'react-redux';
import '@ant-design/v5-patch-for-react-19';
import './index.scss';
import App from './App';
import store from './store';
// import reportWebVitals from './reportWebVitals';

ReactDOM.createRoot(document.getElementById('root')).render(
    <Provider store={store}>
      <App/>
    </Provider>,
);

// reportWebVitals();

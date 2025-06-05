import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';

import './index.scss';
import App from './App';
import store from './store';
// import reportWebVitals from './reportWebVitals';

ReactDOM.createRoot(document.getElementById('root')).render(
    <Provider store={store}>
        <App />
    </Provider>
);

// reportWebVitals();

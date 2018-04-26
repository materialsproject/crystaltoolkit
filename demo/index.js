import React from 'react';
import ReactDOM from 'react-dom';

import Demo from './Demo.react';

// Fix for rendering React externally:
// See https://github.com/gaearon/react-hot-loader/tree/v1.3.1/docs#usage-with-external-react
const rootInstance = ReactDOM.render(
    <Demo/>,
    document.getElementById('react-demo-entry-point')
);

/* eslint-disable */
require('react-hot-loader/Injection').RootInstanceProvider.injectProvider({
/* eslint-enable */
    getRootInstances: function () {
      // Help React Hot Loader figure out the root component instances on the page:
      return [rootInstance];
    }
});

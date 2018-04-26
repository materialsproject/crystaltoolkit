import React, {Component} from 'react';
import {ExampleComponent} from '../src';

class Demo extends Component {
    constructor() {
        super();
        this.state = {
            value: ''
        }
    }

    render() {
        return (
            <div>
                <h1>mp-viewer Demo</h1>

                <hr/>
                <h2>ExampleComponent</h2>
                <ExampleComponent
                    label="This is an example label"
                    value={this.state.value}
                    setProps={newProps => this.setState({value: newProps.value})}
                />
                <hr/>
            </div>
        );
    }
}

export default Demo;

import React from 'react';
import {shallow} from 'enzyme';
import ExampleComponent from '../ExampleComponent.react';

describe('ExampleComponent', () => {

    it('renders', () => {
        const component = shallow(<ExampleComponent label="Test label"/>);
        expect(component).to.be.ok;
    });
});

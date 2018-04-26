import React from 'react';
import {shallow} from 'enzyme';
import StructureViewerComponent from '../StructureViewerComponent.react';

describe('StructureViewerComponent', () => {

    it('renders', () => {
        const component = shallow(<StructureViewerComponent label="Test label"/>);
        expect(component).to.be.ok;
    });
});

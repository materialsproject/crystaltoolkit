import React, {
	Component
} from 'react';
import PropTypes from 'prop-types';
import * as THREE from 'three';
import OrbitControls from 'orbit-controls-es6';
import StructureViewer from './StructureViewer.js';

// DEVELOPER NOTE: This is written by a novice JavaScript/React developer,
// here be dragons.

// TODO: replace all Geometries with BufferGeometries
// TODO: add a prop to animate atoms

/**
 * StructureViewerComponent is ...
 * ...
 */
export default class StructureViewerComponent extends Component {

	constructor(props) {
		super(props)
	}

	componentDidMount() {

	    this.structure_viewer = new StructureViewer(this.props.data, this.mount);

	}

	componentWillUpdate(nextProps, nextState) {

		if (nextProps.data !== this.props.data) {
		    if (this.structure_viewer.crystal !== 'undefined') {
		        this.structure_viewer.replaceCrystal(nextProps.data);
		    } else {
		        this.structure_viewer.addCrystal(nextProps.data);
		    }
		    this.structure_viewer.changeVisibility(nextProps.visibilityOptions);
		}

		if (typeof this.structure_viewer.crystal !== 'undefined') {
			if (nextProps.visibilityOptions != this.props.visibilityOptions) {
			    this.structure_viewer.changeVisibility(nextProps.visibilityOptions)
			}
		}

		if (nextProps.n_screenshot_requests != this.props.n_screenshot_requests) {
		    // this is correct in React?
		    //this.setState({screenshot: this.structure_viewer.renderer.domElement.toDataURL()});
		    //console.log(this.structure_viewer.renderer.domElement.toDataURL());
		    //this.structure_viewer.takeScreenshot();
		}

		if (nextProps.rotationSpeed != this.structure_viewer.rotationSpeed) {
		    this.structure_viewer.rotationSpeed = nextProps.rotationSpeed;
		}

	}

	componentWillUnmount() {
		this.structure_viewer.stop()
		this.structure_viewer.removeCrystal()
		this.mount.removeChild(this.structure_viewer.renderer.domElement)
	}

	render() {
		const {
			id,
			setProps,
			data,
			visibilityOptions
		} = this.props;

		return ( <div id={id}
		style = {
				{
					'width': 'inherit',
					'height': 'inherit'
				}
			}
			ref = {
				(mount) => {
					this.mount = mount
				}
			} >
			</div>
		);
	}
}

StructureViewerComponent.defaultProps = {
    rotationSpeed: 0,
    n_screenshot_requests: 0,
    generationOptions: {}
}

StructureViewerComponent.propTypes = {
	/**
	 * The ID used to identify this compnent in Dash callbacks
	 */
	id: PropTypes.string,

	/**
	 * JSON describing the visualization of the crystal structure, generated
	 * by pymatgen's MaterialsProjectStructureVis class
	 */
	data: PropTypes.object,

	/**
	 * The pymatgen Structure, stored for convenience (not used internally by viewer)
	 */
	value: PropTypes.object,

	/**
	 * Options used for generating visualization, stored for convenience (not used internally by viewer)
	 */
	generationOptions: PropTypes.object,

	/**
	 * Whether or not to display atoms, bonds, etc.
	 * (This also includes specific polyhedra tags, might
	 *  separate this into a separate prop later)
	 */
	visibilityOptions: PropTypes.object,

	/**
	 * Amount to rotate about y-axis per frame
	 *
	 */
	rotationSpeed: PropTypes.number,

	/**
	 * Dash-assigned callback that should be called whenever any of the
	 * properties change
	 */
	setProps: PropTypes.func,

	/**
	 * Increment to trigger a screenshot request
	 */
	n_screenshot_requests: PropTypes.number,

	/**
	 * Screenshot as PNG data URI.
	 */
	screenshot: PropTypes.string
};

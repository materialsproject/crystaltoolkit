import React, {
	Component
} from 'react';
import PropTypes from 'prop-types';
import MP3D from './MP3D.js';

/**
 * MP3DComponent is ...
 * ...
 */
export default class MP3DComponent extends Component {

	constructor(props) {
		super(props)
	}

	componentDidMount() {

	    this.viewer = new MP3D(this.props.data, this.mount, this.props.settings);

	}

	componentWillUpdate(nextProps, nextState) {

	}

	componentWillUnmount() {
	    this.viewer.stop();
		this.mount.removeChild(this.viewer.renderer.domElement);
	}

	render() {
		const {
			id,
			setProps,
			data,
			settings
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


MP3DComponent.propTypes = {
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
	 * Options used for generating scene
	 */
	settings: PropTypes.object,

	/**
	 * Dash-assigned callback that should be called whenever any of the
	 * properties change
	 */
	setProps: PropTypes.func,

};

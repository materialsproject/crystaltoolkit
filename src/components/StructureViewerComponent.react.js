import React, {
	Component
} from 'react';
import PropTypes from 'prop-types';
import * as THREE from 'three';
import OrbitControls from 'orbit-controls-es6';

/**
 * StructureViewerComponent is an example component.
 * It takes a property, `label`, and
 * displays it.
 * It renders an input with the property `value`
 * which is editable by the user.
 */
export default class StructureViewerComponent extends Component {

	makeCrystal(crystal_json) {

		const crystal = new THREE.Object3D();
		crystal.name = 'crystal';
		crystal.castsShadow = true;
		crystal.receivesShadow = true;

		const atoms = this.makeAtoms(crystal_json)
		crystal.add(atoms)

		const bonds = this.makeBonds(crystal_json, atoms)
		crystal.add(bonds)

		//const unit_cell = this.makeUnitCell(crystal_json)
		//crystal.add(unit_cell)

		//const polyhedra = this.makePolyhedra(crystal_json, atoms)
		//crystal.add(polyhedra)
		return crystal

	}

	static getMaterial(color) {
		return new THREE.MeshPhongMaterial({
			color: color,
			shininess: 1,
			reflectivity: 0.5,
			specular: 0xffffff
		});
	}

	makeAtoms(crystal_json) {

		const scale = 0.5;

		const atoms = new THREE.Object3D();
		atoms.name = 'atoms';

		crystal_json.atoms.forEach(function(atom) {
			const radius = atom.fragments[0].radius * scale;
			const geometry = new THREE.SphereGeometry(radius, 32, 32);
			const color = new THREE.Color(...atom.fragments[0].color);
			const material = StructureViewerComponent.getMaterial(color);
			const sphere = new THREE.Mesh(geometry, material);
			sphere.position.set(...atom.position)
			atoms.add(sphere);
		});

		return atoms;
	}

	makeBonds(crystal_json, atoms) {

		const bonds = new THREE.Object3D();
		bonds.name = 'bonds';

		crystal_json.bonds.forEach(function(bond) {

			const sourceObj = atoms.children[bond.from_atom_index]
			const destinationObj = atoms.children[bond.to_atom_index]

			var midPoint = destinationObj.position.clone().sub(sourceObj.position);
			const len = midPoint.length();
			midPoint = midPoint.multiplyScalar(0.5);
			midPoint = sourceObj.position.clone().add(midPoint)

			const geometry = new THREE.CylinderGeometry(0.1, 0.1, len / 2, 16, 1);

			geometry.applyMatrix(new THREE.Matrix4().makeTranslation(0, len / 4, 0));
			geometry.applyMatrix(new THREE.Matrix4().makeRotationX(Math.PI / 2));

			const material_from = StructureViewerComponent.getMaterial(atoms.children[bond.from_atom_index].material.color);

			const cylinder_from = new THREE.Mesh(geometry, material_from);

			cylinder_from.translateX(sourceObj.position.x);
			cylinder_from.translateY(sourceObj.position.y);
			cylinder_from.translateZ(sourceObj.position.z);

			cylinder_from.lookAt(midPoint);

			const material_to = StructureViewerComponent.getMaterial(atoms.children[bond.to_atom_index].material.color);

			const cylinder_to = new THREE.Mesh(geometry, material_to);
			cylinder_to.translateX(destinationObj.position.x);
			cylinder_to.translateY(destinationObj.position.y);
			cylinder_to.translateZ(destinationObj.position.z);

			cylinder_to.lookAt(midPoint);

			bonds.add(cylinder_from);
			bonds.add(cylinder_to);

		})

		return bonds;

	}

	//makeUnitCell(crystal_json){
	//
	//    const points = crystal_json.unit_cell.points.map(p => new THREE.Vector3(...p))
	//
	//    const unitcell_geometry = new THREE.ConvexGeometry( points );
	//    const unitcell_material = new THREE.MeshBasicMaterial( {color: 0x00ff00, transparent: true, opacity: 0.5} );
	//    const edges = new THREE.EdgesGeometry( unitcell_geometry );
	//
	//    const unitcell = new THREE.LineSegments( edges, new THREE.LineBasicMaterial( { color: 0x0 } ) );
	//    unitcell.name = 'unitcell';
	//
	//    return unitcell
	//}


	constructor(props) {
		super(props)

		this.start = this.start.bind(this)
		this.stop = this.stop.bind(this)
		this.animate = this.animate.bind(this)
	}

	componentDidMount() {

		// This is where all the Three.js scene construction happens

		const width = this.mount.clientWidth
		const height = this.mount.clientHeight

		const scene = new THREE.Scene()
		const camera = new THREE.OrthographicCamera(
			width / -2,
			width / 2,
			height / 2,
			height / -2,
			-2000, 2000);

		camera.position.z = 2;

		const renderer = new THREE.WebGLRenderer({
			antialias: true,
			alpha: true
		})

		renderer.setPixelRatio(window.devicePixelRatio * 1.5);
		renderer.setClearColor(0xffffff, 0)
		renderer.setSize(width, height)

		// Lighting

		const ambientLight = new THREE.AmbientLight(0x555555, 0.002);
		scene.add(ambientLight)

		const directionalLight = new THREE.DirectionalLight(0xFFFFFF, 0.0015);
		directionalLight.position.set(-1, 1, 1).normalize();
		scene.add(directionalLight);
		scene.add(directionalLight.target);

		const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x222222, 0.003);
		scene.add(hemisphereLight)

		const pointLight = new THREE.PointLight(0xffffff);
		camera.add(pointLight)

		if (typeof this.crystal !== 'undefined') {

			const crystal = this.crystal;

			scene.add(crystal);
			camera.lookAt(crystal.position);
			directionalLight.target = crystal;

			const box = new THREE.Box3();
			box.setFromObject(crystal);
			camera.zoom = Math.min(width / (box.max.x - box.min.x),
				height / (box.max.y - box.min.y)) * 0.6;
			camera.updateProjectionMatrix();
			camera.updateMatrix();

			this.crystal = crystal;
		}

		this.scene = scene
		this.camera = camera
		this.renderer = renderer

		// Controls
		var controls = new OrbitControls(camera, this.renderer.domElement);

		this.mount.appendChild(this.renderer.domElement)
		this.start();
		
	}
	
	componentWillUpdate(nextProps, nextState){
		
		
		const atoms = this.scene.getObjectByName('atoms');
		atoms.visible = nextProps.showAtoms;
		
		//if (typeof data !== 'undefined') {
		//	const oldCrystal = self.scene.getObjectByName('crystal');
		//	self.scene.remove(oldCrystal); 
		//	//this.crystal = this.makeCrystal(data);
		//	//self.scene.add(this.crystal);
		//	
		//}
		
	}

	componentWillUnmount() {
		this.stop()
		this.mount.removeChild(this.renderer.domElement)
	}

	start() {
		if (!this.frameId) {
			this.frameId = requestAnimationFrame(this.animate)
		}
	}

	stop() {
		cancelAnimationFrame(this.frameId)
	}

	animate() {
		this.renderScene()
		this.frameId = window.requestAnimationFrame(this.animate)
	}

	renderScene() {
		this.renderer.render(this.scene, this.camera)
	}

	render() {
		const {
			id,
			setProps,
			data,
			showAtoms
		} = this.props;
		
		if (typeof data !== 'undefined') {
			this.crystal = this.makeCrystal(data);
		}

		return ( <
			div id = {
				id
			}
			style = {
				{
					'width': '100%',
					'padding-bottom': '75%'
				}
			}
			ref = {
				(mount) => {
					this.mount = mount
				}
			} >
			<
			/div>
		);
	}
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
	 * Whether or not to display atoms
	 *
	 */
	showAtoms: PropTypes.bool,
	
	/**
	 * Dash-assigned callback that should be called whenever any of the
	 * properties change
	 */
	setProps: PropTypes.func
};

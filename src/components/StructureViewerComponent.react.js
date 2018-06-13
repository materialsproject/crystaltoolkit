import React, {
	Component
} from 'react';
import PropTypes from 'prop-types';
import * as THREE from 'three';
import OrbitControls from 'orbit-controls-es6';

// DEVELOPER NOTE: This is written by a novice JavaScript/React developer,
// here be dragons.

// TODO: replace all Geometries with BufferGeometries
// TODO: add a prop to animate atoms

/**
 * StructureViewerComponent is ...
 * ...
 */
export default class StructureViewerComponent extends Component {

	makeCrystal(crystal_json) {

		if (typeof crystal_json !== 'undefined') {


			const crystal = new THREE.Object3D();
			crystal.name = 'crystal';
			crystal.castsShadow = true;
			crystal.receivesShadow = true;

			const atoms = this.makeAtoms(crystal_json)
			crystal.add(atoms)

			const bonds = this.makeBonds(crystal_json, atoms)
			crystal.add(bonds)

			const unit_cell = this.makeUnitCell(crystal_json)
			crystal.add(unit_cell)

			const polyhedra = this.makePolyhedra(crystal_json, atoms)
			crystal.add(polyhedra)

			return crystal

		}

	}

	static getMaterial(color) {
		return new THREE.MeshPhongMaterial({
			color: color,
			shininess: 1,
			reflectivity: 1,
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

	makeUnitCell(crystal_json) {

		const edges = new THREE.Geometry();
		crystal_json.unit_cell.lines.map(p => edges.vertices.push(new THREE.Vector3(...p)))

		const unitcell = new THREE.LineSegments(edges,
			new THREE.LineBasicMaterial({
				color: 0x0,
				linewidth: 1
			}));
		unitcell.name = 'unitcell';

		return unitcell
	}

	makePolyhedra(crystal_json, atoms) {

		const polyhedra = new THREE.Object3D();
		polyhedra.name = 'polyhedra';
		
		this.available_polyhedra = crystal_json.polyhedra.polyhedra_types

		crystal_json.polyhedra.polyhedra_list.forEach(function(polyhedron) {

			const polyhedron_geometry = new THREE.Geometry();
			polyhedron.points.map(p => polyhedron_geometry.vertices.push(new THREE.Vector3(...p)))
			polyhedron.hull.map(p => polyhedron_geometry.faces.push(new THREE.Face3(...p)))
			polyhedron_geometry.computeFaceNormals();

			const polyhedron_color = atoms.children[polyhedron.center].material.color;
			const polyhedron_material = StructureViewerComponent.getMaterial(polyhedron_color);
            polyhedron_material.side = THREE.DoubleSide;

			const polyhedron_object = new THREE.Mesh(polyhedron_geometry, polyhedron_material)

			polyhedron_object.name = polyhedron.name

			polyhedra.add(polyhedron_object)

		})

		return polyhedra

	}

	disposeNode(parentObject) {
	// https://stackoverflow.com/questions/33152132/
        parentObject.traverse(function (node) {
            if (node instanceof THREE.Mesh) {
                if (node.geometry) {
                    node.geometry.dispose();
                }
                if (node.material) {
                    var materialArray;
                    if (node.material instanceof THREE.MeshFaceMaterial || node.material instanceof THREE.MultiMaterial) {
                        materialArray = node.material.materials;
                    }
                    else if(node.material instanceof Array) {
                        materialArray = node.material;
                    }
                    if(materialArray) {
                        materialArray.forEach(function (mtrl, idx) {
                            if (mtrl.map) mtrl.map.dispose();
                            if (mtrl.lightMap) mtrl.lightMap.dispose();
                            if (mtrl.bumpMap) mtrl.bumpMap.dispose();
                            if (mtrl.normalMap) mtrl.normalMap.dispose();
                            if (mtrl.specularMap) mtrl.specularMap.dispose();
                            if (mtrl.envMap) mtrl.envMap.dispose();
                            mtrl.dispose();
                        });
                    }
                    else {
                        if (node.material.map) node.material.map.dispose();
                        if (node.material.lightMap) node.material.lightMap.dispose();
                        if (node.material.bumpMap) node.material.bumpMap.dispose();
                        if (node.material.normalMap) node.material.normalMap.dispose();
                        if (node.material.specularMap) node.material.specularMap.dispose();
                        if (node.material.envMap) node.material.envMap.dispose();
                        node.material.dispose();
                    }
                }
            }
        });
    }


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
			height / -2, -2000, 2000);

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

		const pointLight = new THREE.PointLight(0xffffff, 1.2);
		camera.add(pointLight)

		if (typeof this.props.data !== 'undefined') {

			const crystal = this.makeCrystal(this.props.data);

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
		const controls = new OrbitControls(camera, this.renderer.domElement);

		this.mount.appendChild(this.renderer.domElement)
		this.start();

	}

	componentWillUpdate(nextProps, nextState) {

		if (nextProps.data !== this.props.data) {
			if (typeof this.scene !== 'undefined') {
				var oldCrystal = this.scene.getObjectByName('crystal');
				this.scene.remove(oldCrystal);
				this.disposeNode(oldCrystal);
				this.crystal = this.makeCrystal(nextProps.data);
				this.scene.add(this.crystal);
			}
		}

		if (typeof this.crystal !== 'undefined') {
			var all_options = ['atoms', 'bonds', 'unitcell', 'polyhedra']
			if (typeof this.available_polyhedra !== 'undefined') {
				all_options.push(...this.available_polyhedra)
			}
			const crystal = this.crystal
			if (nextProps.visibilityOptions != this.props.visibilityOptions) {
				all_options.forEach(function(option) {
					var object = crystal.getObjectByName(option);
					if (typeof object !== "undefined") {
						object.visible = nextProps.visibilityOptions.includes(option)
					}
				})
			}
		}

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
		//this.crystal.rotation.y += 0.002;
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
	 * Whether or not to display atoms, bonds, etc.
	 *
	 */
	visibilityOptions: PropTypes.array,

	/**
	 * Dash-assigned callback that should be called whenever any of the
	 * properties change
	 */
	setProps: PropTypes.func
};

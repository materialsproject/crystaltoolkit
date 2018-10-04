import * as THREE from "three";
import OrbitControls from "orbit-controls-es6";

export default class StructureViewer {

    // cheap scene definition
    // eventually should just use the native Three.js scene definition

    //static scene_defaults() {
    //    return {
    //        'lights': [
    //            {
    //                'type': 'hemisphere',
    //                'args': ['#ffffff', '#222222', 0.0025],
    //            },
    //            {
    //                'type': 'directional',
    //                'args': ['#ffffff', 0.0015],
    //                'position': [-50, 50, 50],
    //            },
    //            {
    //                'type': 'ambient',
    //                'args': ['#222222', 0.004]
    //            }
    //        ],
    //        'materials': {
    //            'default': {
    //                'type': 'StandardMaterial',
    //                'parameters': {
    //                    'roughness': 0.05,
    //                    'metalness': 0.00
    //                }
    //            },
    //            'polyhedra': {
    //                'parameters': {
    //                    'opacity': 0.5
    //                }
    //            }
    //        },
    //        'quality': {
    //            'pixelRatio': 1.5,
    //            'segments': 32,
    //            'shadows': true,
    //            'reflections': true
    //        }
    //    }
    //};

    static getMaterial(color) {
        // if we don't have a specific material defined,
        // use the default one

        return new THREE.MeshStandardMaterial({
            color: color,
            roughness: 0.2,
            metalness: 0.0
        })
    }

    static makeCrystal(crystal_json) {
        if (typeof crystal_json !== "undefined" && Object.keys(crystal_json).length !== 0) {
            const crystal = new THREE.Object3D();
            crystal.name = "crystal";

            const atoms = StructureViewer.makeAtoms(crystal_json);
            crystal.add(atoms);

            const bonds = StructureViewer.makeBonds(crystal_json, atoms);
            crystal.add(bonds);

            const unit_cell = StructureViewer.makeUnitCell(crystal_json);
            crystal.add(unit_cell);

            const polyhedra = StructureViewer.makePolyhedra(crystal_json, atoms);
            crystal.add(polyhedra);

            return crystal;
        }
    }

    static makeAtoms(crystal_json) {
        const scale = 0.5;

        const atoms = new THREE.Object3D();
        atoms.name = "atoms";

        crystal_json.atoms.forEach(function (atom) {
            const atomObject = new THREE.Object3D();
            atom.fragments.forEach(function (fragment) {
                const radius = fragment.radius * scale;
                const geometry = new THREE.SphereGeometry(radius, 32, 32, fragment.phi_start, fragment.phi_end - fragment.phi_start);
                const color = new THREE.Color(...fragment.color);
                const material = StructureViewer.getMaterial(color);
                material.side = THREE.DoubleSide;
                const sphereSegment = new THREE.Mesh(geometry, material);
                sphereSegment.receiveShadow = StructureViewer.sceneDefaults().quality.shadow;
                sphereSegment.castShadow = StructureViewer.sceneDefaults().quality.shadow;
                atomObject.add(sphereSegment);
            });
            atomObject.position.set(...atom.position);
            atoms.add(atomObject);
        });

        return atoms;
    }

    static makeBonds(crystal_json, atoms) {
        const bonds = new THREE.Object3D();
        bonds.name = "bonds";

        crystal_json.bonds.forEach(function (bond) {
            const sourceObj = atoms.children[bond.from_atom_index];
            const destinationObj = atoms.children[bond.to_atom_index];

            var midPoint = destinationObj.position.clone().sub(sourceObj.position);
            const len = midPoint.length();
            midPoint = midPoint.multiplyScalar(0.5);
            midPoint = sourceObj.position.clone().add(midPoint);

            const geometry = new THREE.CylinderGeometry(0.1, 0.1, len / 2, 8, 1);

            geometry.applyMatrix(new THREE.Matrix4().makeTranslation(0, len / 4, 0));
            geometry.applyMatrix(new THREE.Matrix4().makeRotationX(Math.PI / 2));

            const material_from = StructureViewer.getMaterial(
                atoms.children[bond.from_atom_index].children[0].material.color
            );

            const cylinder_from = new THREE.Mesh(geometry, material_from);

            cylinder_from.translateX(sourceObj.position.x);
            cylinder_from.translateY(sourceObj.position.y);
            cylinder_from.translateZ(sourceObj.position.z);

            cylinder_from.lookAt(midPoint);

            const material_to = StructureViewer.getMaterial(
                atoms.children[bond.to_atom_index].children[0].material.color
            );

            const cylinder_to = new THREE.Mesh(geometry, material_to);
            cylinder_to.translateX(destinationObj.position.x);
            cylinder_to.translateY(destinationObj.position.y);
            cylinder_to.translateZ(destinationObj.position.z);

            cylinder_to.lookAt(midPoint);

            bonds.add(cylinder_from);
            bonds.add(cylinder_to);
        });

        return bonds;
    }

    static makeUnitCell(crystal_json) {
        const unitcell = new THREE.Object3D();
        unitcell.name = "unitcell";

        for (var cell in crystal_json.unit_cell) {
            const edges = new THREE.Geometry();
            crystal_json.unit_cell[cell].lines.map(p =>
                edges.vertices.push(new THREE.Vector3(...p))
            );

            if (crystal_json.unit_cell[cell].style != "dashed") {
                const line_material = new THREE.LineDashedMaterial({
                    color: 0x0,
                    linewidth: 1,
                    scale: 1,
                    dashSize: 3,
                    gapSize: 1
                });
                const unitcell_object = new THREE.LineSegments(edges, line_material);
                unitcell.add(unitcell_object);
            } else {
                const line_material = new THREE.LineBasicMaterial({
                    color: 0x0,
                    linewidth: 1
                });
                const unitcell_object = new THREE.LineSegments(edges, line_material);
                unitcell.add(unitcell_object);
            }
        }

        return unitcell;
    }

    static makePolyhedra(crystal_json, atoms) {
        const polyhedra = new THREE.Object3D();
        polyhedra.name = "polyhedra";

        this.available_polyhedra = crystal_json.polyhedra.polyhedra_types;
        this.default_polyhedra = crystal_json.polyhedra.default_polyhedra_types;

        for (var polyhedron_type in crystal_json.polyhedra.polyhedra_by_type) {
            const polyhedra_type_object = new THREE.Object3D();
            polyhedra_type_object.name = polyhedron_type;

            crystal_json.polyhedra.polyhedra_by_type[polyhedron_type].forEach(
                function (polyhedron) {
                    const polyhedron_geometry = new THREE.Geometry();
                    polyhedron.points.map(p =>
                        polyhedron_geometry.vertices.push(new THREE.Vector3(...p))
                    );
                    polyhedron.hull.map(p =>
                        polyhedron_geometry.faces.push(new THREE.Face3(...p))
                    );
                    polyhedron_geometry.computeFaceNormals();

                    const polyhedron_color =
                        atoms.children[polyhedron.center].children[0].material.color;
                    const polyhedron_material = StructureViewer.getMaterial(
                        polyhedron_color
                    );
                    polyhedron_material.opacity = 0.5;
                    polyhedron_material.side = THREE.DoubleSide;
                    polyhedron_material.transparent = true;
                    polyhedron_material.depthWrite = false;

                    const polyhedron_object = new THREE.Mesh(
                        polyhedron_geometry,
                        polyhedron_material
                    );

                    polyhedron_object.transparent = true;

                    polyhedra_type_object.add(polyhedron_object);
                }
            );

            if (!this.default_polyhedra.includes(polyhedron_type)) {
                polyhedra_type_object.visible = false;
            }

            polyhedra.add(polyhedra_type_object);
        }

        return polyhedra;
    }

    constructor(crystal_json, dom_elt, rotationSpeed = 0, settings) {

        const defaults = {
            quality: {
                shadows: true,
                transparency: true,
                antialias: true,
                transparent_background: true,
                pixelRatio: 1.5,
                sphere_segments: 32,
                reflections: false
            }
        };
        this.settings = Object.assign(defaults, settings);

        this.start = this.start.bind(this);
        this.stop = this.stop.bind(this);
        this.animate = this.animate.bind(this);
        this.rotationSpeed = rotationSpeed;

        // This is where all the Three.js scene construction happens

        const width = dom_elt.clientWidth;
        const height = dom_elt.clientHeight;

        const scene = new THREE.Scene();
        const camera = new THREE.OrthographicCamera(
            width / -2,
            width / 2,
            height / 2,
            height / -2,
            -2000,
            2000
        );

        camera.position.z = 2;

        const renderer = new THREE.WebGLRenderer({
            antialias: this.settings.quality.antialias,
            alpha: this.settings.quality.transparent_background,
            gammaInput: true,
            gammaOutput: true,
            gammaFactor: 2.2,
            shadowMapEnabled: true
        });

        renderer.setPixelRatio(window.devicePixelRatio * this.settings.quality.pixelRatio);
        renderer.setClearColor(0xffffff, 0);
        renderer.setSize(width, height);

        // Lighting

        const ambientLight = new THREE.AmbientLight(0x222222, 0.015);
        camera.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.003);
        directionalLight.position.set(-2, 2, 2);
        directionalLight.castsShadow = StructureViewer.sceneDefaults().quality.shadows;
        camera.add(directionalLight);

        const hemisphereLight = new THREE.HemisphereLight(
            0xffffff,
            0x222222,
            0.0025
        );
        //camera.add(hemisphereLight);

        // Helpers (for positioning lights, not for production)
        const directionalLightHelper = new THREE.DirectionalLightHelper(directionalLight, 2, 0x0000ff);
        scene.add(directionalLightHelper);

        scene.add(camera);

        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        //this.directionalLight = directionalLight;

        const cubeCamera = new THREE.CubeCamera(0.1, 10, 512);
        this.cubeCamera = cubeCamera.renderTarget.texture;
        scene.add(cubeCamera);


        // Controls
        const controls = new OrbitControls(camera, this.renderer.domElement);
        controls.enableKeys = false;

        dom_elt.appendChild(this.renderer.domElement);
        this.start();

        this.addCrystal(crystal_json);

        //console.log(JSON.stringify(scene.toJSON()));
    }

    changeVisibility(visibilityOptions) {

        if (typeof this.crystal !== "undefined") {
            var atoms = this.crystal.getObjectByName("atoms");
            if (typeof atoms !== "undefined") {
                if (visibilityOptions.atoms) {
                    atoms.visible = true;
                } else {
                    atoms.visible = false;
                }
            }

            var bonds = this.crystal.getObjectByName("bonds");
            if (typeof bonds !== "undefined") {
                if (visibilityOptions.bonds) {
                    bonds.visible = true;
                } else {
                    bonds.visible = false;
                }
            }

            var unitcell = this.crystal.getObjectByName("unitcell");
            if (typeof unitcell !== "undefined") {
                if (visibilityOptions.unitcell) {
                    unitcell.visible = true;
                } else {
                    unitcell.visible = false;
                }
            }

            var polyhedra = this.crystal.getObjectByName("polyhedra");
            if (typeof polyhedra !== "undefined") {
                if (visibilityOptions.polyhedra instanceof Array) {
                    polyhedra.visible = true;
                    for (var polyhedraType in this.available_polyhedra) {
                        var polyhedraTypeObject = this.crystal.getObjectByName(polyhedraType);
                        if (polyhedraType in visibilityOptions.polyhedra) {
                            polyhedraTypeObject.visible = true;
                        } else {
                            polyhedraTypeObject.visible = false;
                        }
                    }
                } else if (visibilityOptions.polyhedra) {
                    polyhedra.visible = true;
                } else {
                    polyhedra.visible = false;
                }
            }
        }
    }

    showVectors(vector_list) {
        // TODO
    }

    showEllipsoids(ellipsoid_list) {
        // TODO
    }

    changeColorScheme(new_scheme) {
        // TODO
    }

    setQuality(quality) {
        // TODO
        // can tweak geometry detail, pixel ratio, antialias (int ? from 0-100)

    }


    static disposeNode(parentObject) {
        // https://stackoverflow.com/questions/33152132/
        parentObject.traverse(function (node) {
            if (node instanceof THREE.Mesh) {
                if (node.geometry) {
                    node.geometry.dispose();
                }
                if (node.material) {
                    var materialArray;
                    if (
                        node.material instanceof THREE.MeshFaceMaterial ||
                        node.material instanceof THREE.MultiMaterial
                    ) {
                        materialArray = node.material.materials;
                    } else if (node.material instanceof Array) {
                        materialArray = node.material;
                    }
                    if (materialArray) {
                        materialArray.forEach(function (mtrl, idx) {
                            if (mtrl.map) mtrl.map.dispose();
                            if (mtrl.lightMap) mtrl.lightMap.dispose();
                            if (mtrl.bumpMap) mtrl.bumpMap.dispose();
                            if (mtrl.normalMap) mtrl.normalMap.dispose();
                            if (mtrl.specularMap) mtrl.specularMap.dispose();
                            if (mtrl.envMap) mtrl.envMap.dispose();
                            mtrl.dispose();
                        });
                    } else {
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

    addCrystal(crystal_json) {
        if (typeof crystal_json !== "undefined" && Object.keys(crystal_json).length !== 0) {
            const crystal = StructureViewer.makeCrystal(crystal_json);

            this.scene.add(crystal);
            this.camera.lookAt(crystal.position);
            //this.directionalLight.target = crystal;

            const box = new THREE.Box3();
            box.setFromObject(crystal);
            const width = this.renderer.domElement.clientWidth;
            const height = this.renderer.domElement.clientHeight;
            this.camera.zoom =
                Math.min(
                    width / (box.max.x - box.min.x),
                    height / (box.max.y - box.min.y)
                ) * 0.5;
            this.camera.updateProjectionMatrix();
            this.camera.updateMatrix();

            this.crystal = crystal;
            this.available_polyhedra = crystal_json.polyhedra.polyhedra_types;
        }
    }

    removeCrystal() {
        if (typeof this.scene !== "undefined" && typeof this.crystal !== "undefined") {
            var oldCrystal = this.scene.getObjectByName("crystal");
            this.scene.remove(oldCrystal);
            StructureViewer.disposeNode(oldCrystal);
            delete this.crystal;
        }
    }

    replaceCrystal(crystal_json) {
        if (typeof this.scene !== "undefined" && typeof this.crystal !== "undefined") {
            this.removeCrystal();
            this.addCrystal(crystal_json);
        }
    }

    start() {
        if (!this.frameId) {
            this.frameId = requestAnimationFrame(this.animate);
        }
    }

    stop() {
        cancelAnimationFrame(this.frameId);
    }

    animate() {
        if (typeof this.crystal !== "undefined") {
            this.crystal.rotation.y += this.rotationSpeed;
        }
        this.renderScene();
        this.frameId = window.requestAnimationFrame(this.animate);
    }

    renderScene() {
        this.renderer.render(this.scene, this.camera);
    }

    takeScreenshot() {
        this.renderScene();
        window.open(this.renderer.domElement.toDataURL("image/png"), "Final");
    }
}

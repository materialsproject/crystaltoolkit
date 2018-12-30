import * as THREE from "three-full";

export default class Simple3DScene {

    constructor(scene_json, dom_elt, settings) {

        this.start = this.start.bind(this);
        this.stop = this.stop.bind(this);
        this.animate = this.animate.bind(this);

        const defaults = {
            quality: {
                shadows: true,
                transparency: true,
                antialias: true,
                transparent_background: true,
                pixelRatio: 1.5,
                sphereSegments: 32,
                cylinderSegments: 8,
                reflections: false
            },
            other: {
                autorotate: true,
                sphereScale: 1.0,
                cylinderScale: 1.0
            },
            lights: [
                {
                    type: 'DirectionalLight',
                    args: ["#ffffff", 0.003],
                    position: [-2, 2, 2]
                },
                {
                    type: 'AmbientLight',
                    args: ['#222222', 0.015],
                    position: [10, 10, 10]

                },
                {
                    type: 'HemisphereLight',
                    args: ['#ffffff', '#222222', 0.0025]
                }
            ],
            material: {
                type: 'MeshStandardMaterial',
                parameters: {
                    roughness: 0.2,
                    metalness: 0.0
                }
            }
        };

        this.settings = Object.assign(defaults, settings);

        // Stage

        const width = dom_elt.clientWidth;
        const height = dom_elt.clientHeight;

        const renderer = new THREE.WebGLRenderer({
            antialias: this.settings.quality.antialias,
            alpha: this.settings.quality.transparent_background,
            gammaInput: true,
            gammaOutput: true,
            gammaFactor: 2.2,
        });
        this.renderer = renderer;

        renderer.setPixelRatio(window.devicePixelRatio * this.settings.quality.pixelRatio);
        renderer.setClearColor(0xffffff, 0);
        renderer.setSize(width, height);

        const scene = new THREE.Scene();
        this.scene = scene;

        // Camera

        // TODO: change so camera dimensions match scene, not dom_elt?
        const camera = new THREE.OrthographicCamera(
            width / -2,
            width / 2,
            height / 2,
            height / -2,
            -2000,
            2000
        );
        // need to offset for OrbitControls
        camera.position.z = 2;

        this.camera = camera;
        scene.add(camera);

        // Lights

        this.makeLights(scene, this.settings.lights);

        // Action

        this.addToScene(scene_json);

        const controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        controls.enableKeys = false;

        dom_elt.appendChild(renderer.domElement);
        this.start();

        // allow resize
        //function onWindowResize(){
        //    // not implemented
        //}
        //window.addEventListener( 'resize', onWindowResize, false );
    }

    downloadScreenshot(filename) {

        // using method from Three.js editor

        // create a link and hide it from end-user
        var link = document.createElement( 'a' );
	    link.style.display = 'none';
	    document.body.appendChild( link );

	    // force a render (in case buffer has been cleared)
        this.renderScene();
        // and set link href to renderer contents
		link.href = this.renderer.domElement.toDataURL("image/png"); // URL.createObjectURL( blob );

        // click link to download
		link.download = filename || 'screenshot.png';
		link.click();

    }

    addToScene(scene_json) {

        Simple3DScene.disposeNodebyName(this.scene, scene_json.name);

        const root_obj = new THREE.Object3D();
        root_obj.name = scene_json.name;

        function traverse_scene(o, parent, self) {
            o.contents.forEach(function (sub_o) {
                if (sub_o.hasOwnProperty('type')) {
                    parent.add(self.makeObject(sub_o));
                } else {
                    let new_parent = new THREE.Object3D();
                    new_parent.name = sub_o.name;
                    parent.add(new_parent);
                    traverse_scene(sub_o, new_parent, self);
                }
            });
        }

        traverse_scene(scene_json, root_obj, this);

        window.console.log(root_obj);

        this.scene.add(root_obj);

    }

     makeLights(scene, light_json) {

        Simple3DScene.disposeNodebyName(scene, 'lights');

        const lights = new THREE.Object3D();
        lights.name = 'lights';

        light_json.forEach(function (light) {
            switch (light.type) {
                case "DirectionalLight":
                    var lightObj = new THREE.DirectionalLight(...light.args);
                    if (light.helper) {
                        let lightHelper = new THREE.DirectionalLightHelper(lightObj, 5, '#ffff00');
                        lightObj.add(lightHelper);
                    }
                    break;
                case "AmbientLight":
                    var lightObj = new THREE.AmbientLight(...light.args);
                    break;
                case "HemisphereLight":
                    var lightObj = new THREE.HemisphereLight(...light.args);
                    break;
            }
            if (light.hasOwnProperty('position')) {
                lightObj.position.set(...light.position);
            }
            lights.add(lightObj);
        });

        window.console.log("lights", lights);

        scene.add(lights);

    }

    makeObject(object_json) {

        const obj = new THREE.Object3D();
        obj.name = object_json.name;

        switch (object_json.type) {
            case "spheres": {

                const geom = new THREE.SphereBufferGeometry(
                    object_json.radius * this.settings.other.sphereScale,
                    this.settings.quality.sphereSegments,
                    this.settings.quality.sphereSegments,
                    object_json.phiStart || 0,
                    object_json.phiEnd || Math.PI * 2
                );
                const mat = this.makeMaterial(object_json.color);

                const meshes = [];
                object_json.positions.forEach(function (position) {
                    const mesh = new THREE.Mesh(geom, mat);
                    mesh.position.set(...position);
                    meshes.push(mesh);
                });

                // TODO: test axes are correct!
                if (object_json.ellipsoids) {
                    const vec_z = new THREE.Vector3(0, 0, 1);
                    const quaternion = new THREE.Quaternion();
                    object_json.ellipsoids.rotations.forEach(function (rotation, index){
                        const rotation_vec = new THREE.Vector3(...rotation);
                        quaternion.setFromUnitVectors(
                            vec_z,
                            rotation_vec.normalize()
                        );
                        meshes[index].setRotationFromQuaternion( quaternion);
                    });
                    object_json.ellipsoids.scales.forEach(function (scale, index){
                        meshes[index].scale.set(...scale);
                    });
                }

                meshes.forEach(function (mesh) {
                   obj.add(mesh);
                });

                return obj;
            }
            case "cylinders": {

                const radius = object_json.radius || 1;

                const geom = new THREE.CylinderBufferGeometry(
                    radius * this.settings.other.cylinderScale,
                    radius * this.settings.other.cylinderScale,
                    1.0,
                    this.settings.quality.cylinderSegments
                );
                const mat = this.makeMaterial(object_json.color);

                object_json.positionPairs.forEach(function (positionPair) {

                    // the following is technically correct but could be optimized?

                    const mesh = new THREE.Mesh(geom, mat);
                    const vec_a = new THREE.Vector3(...positionPair[0]);
                    const vec_b = new THREE.Vector3(...positionPair[1]);
                    const vec_rel = vec_b.sub(vec_a);

                    // scale cylinder to correct length
                    mesh.scale.y = vec_rel.length();

                    // set origin at midpoint of cylinder
                    const vec_midpoint = vec_a.add(vec_rel.clone().multiplyScalar(0.5));
                    mesh.position.set(vec_midpoint.x, vec_midpoint.y, vec_midpoint.z);

                    // rotate cylinder into correct orientation
                    const vec_y = new THREE.Vector3(0, 1, 0); // initial axis of cylinder
                    const quaternion = new THREE.Quaternion();
                    quaternion.setFromUnitVectors(
                        vec_y,
                        vec_rel.normalize()
                    );
                    mesh.setRotationFromQuaternion( quaternion );

                    obj.add(mesh);
                });

                return obj
            }
            case "cubes": {
                const geom = new THREE.BoxBufferGeometry(
                    object_json.width * this.settings.other.sphereScale,
                    object_json.width * this.settings.other.sphereScale,
                    object_json.width * this.settings.other.sphereScale
                );
                const mat = this.makeMaterial(object_json.color);

                object_json.positions.forEach(function (position) {
                    const mesh = new THREE.Mesh(geom, mat);
                    mesh.position.set(...position);
                    obj.add(mesh);
                });

                return obj;
            }
            case "lines": {
                const verts = new THREE.Float32BufferAttribute([].concat.apply([], object_json.positions), 3);
                const geom = new THREE.BufferGeometry();
                geom.addAttribute('position', verts);

                let mat;
                if (object_json.dashSize || object_json.scale || object_json.gapSize) {
                    mat = new THREE.LineDashedMaterial({
                        color: object_json.color || '#000000',
                        linewidth: object_json.line_width || 1,
                        scale: object_json.scale || 1,
                        dashSize: object_json.dashSize || 3,
                        gapSize: object_json.gapSize || 1
                    })
                } else {
                    mat = new THREE.LineBasicMaterial({
                        color: object_json.color || '#2c3c54',
                        linewidth: object_json.line_width || 1
                    });
                }

                const mesh = new THREE.LineSegments(geom, mat);
                obj.add(mesh);

                return obj;
            }
            case "surface": {

                const verts = new THREE.Float32BufferAttribute([].concat.apply([], object_json.positions), 3);
                const geom = new THREE.BufferGeometry();
                geom.addAttribute('position', verts);

                const mat = this.makeMaterial(object_json.color, object_json.opacity || 1);

                if (object_json.normals) {
                    const normals = new THREE.Float32BufferAttribute([].concat.apply([], object_json.normals), 3);
                    geom.addAttribute('normal', normals);
                } else {
                    geom.computeFaceNormals();
                    mat.side = THREE.DoubleSide;  // not sure if this is necessary if we compute normals correctly
                }

                if (object_json.opacity) {
                    mat.transparent = true;
                    mat.depthWrite = false;
                }

                const mesh = new THREE.Mesh(geom, mat);
                obj.add(mesh);

                return obj;
            }
            case "convex": {

                const points = object_json.positions.map(p => new THREE.Vector3(...p));
                const geom = new THREE.ConvexBufferGeometry(points);

                const mat = this.makeMaterial(object_json.color, object_json.opacity || 1);
                if (object_json.opacity) {
                    mat.transparent = true;
                    mat.depthWrite = false;
                }

                const mesh = new THREE.Mesh(geom, mat);
                obj.add(mesh);

                return obj;
            }
            case "arrows": {
                // take inspiration from ArrowHelper, user cones and cylinders
                return obj;
            }
            case "labels": {
                // Not implemented
                //THREE.CSS2DObject
                return obj;
            }
            default: {
                return obj;
            }
        }

    }

    makeMaterial(color, opacity) {

        const parameters = Object.assign(this.settings.material.parameters,
                    {color: color || '#52afb0', opacity: opacity || 1.0});

        switch (this.settings.material.type) {
            case "MeshStandardMaterial": {
                return new THREE.MeshStandardMaterial(parameters);
            }
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
        this.renderScene();
        this.frameId = window.requestAnimationFrame(this.animate);
    }

    renderScene() {
        this.renderer.render(this.scene, this.camera);
    }

    toggleVisibility(namesToVisibility) {

        // for names in nodeNameMap ... if 1, show, if 0 hide

    }

    static disposeNodebyName(scene, name) {
        // name is not necessarily unique, make this recursive ?
        let object = scene.getObjectByName(name);
        if (typeof object !== "undefined") {
            Simple3DScene.disposeNode(object);
        }
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

}

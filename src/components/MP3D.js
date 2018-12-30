import * as THREE from "three-full";

export default class MP3D {

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

        this.addToScene(scene, scene_json);

        // light-weight animation system, replace later
        //this.currentAnimationFrame = 0;
        //this.animations = {
        //    '0': [
        //        {'position': new THREE.Vector3(0, 0, 0)},//
        //        {'position': new THREE.Vector3(0, 0, 1)},
        //        {'position': new THREE.Vector3(0, 0, 2)}
        //        ]
        //};

        const controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        controls.enableKeys = false;

        dom_elt.appendChild(renderer.domElement);
        this.start();

        // allow resize

        function onWindowResize(){
        //    //camera.aspect = dom_elt.innerWidth / dom_elt.innerHeight;
        //    //camera.updateProjectionMatrix();
        //    //renderer.setSize( dom_elt.innerWidth, dom_elt.innerHeight );
            console.log( 'dom', renderer.domElement.innerWidth)//, dom_elt.innerHeight );
        }

        window.addEventListener( 'resize', onWindowResize, false );
    }

    addToScene(scene, scene_json) {

        MP3D.disposeNodebyName(scene, scene_json.name);

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

        scene.add(root_obj);

    }

     makeLights(scene, light_json) {

        MP3D.disposeNodebyName(scene, 'lights');

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
            case "sphere": {

                const geom = new THREE.SphereBufferGeometry(
                    object_json.radius * this.settings.other.sphereScale,
                    this.settings.quality.sphereSegments,
                    this.settings.quality.sphereSegments,
                    object_json.phi_start || 0,
                    object_json.phi_end || Math.PI * 2
                );
                const mat = this.makeMaterial(object_json.color);

                object_json.positions.forEach(function (position) {
                    const mesh = new THREE.Mesh(geom, mat);
                    mesh.position.set(...position);
                    obj.add(mesh);
                });

                return obj;
            }
            case "cylinder": {

                const geom = new THREE.CylinderBufferGeometry(
                    object_json.radius * this.settings.other.cylinderScale,
                    object_json.radius * this.settings.other.cylinderScale,
                    1.0,
                    this.settings.quality.cylinderSegments
                );
                const mat = this.makeMaterial(object_json.color);

                object_json.positions.forEach(function (position) {

                    // the following is technically correct but could be optimized?

                    const mesh = new THREE.Mesh(geom, mat);
                    const vec_a = new THREE.Vector3(...position[0]);
                    const vec_b = new THREE.Vector3(...position[1]);
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

                if (object_json.normals) {
                    const normals = new THREE.Float32BufferAttribute([].concat.apply([], object_json.normals), 3);
                    geom.addAttribute('normal', normals);
                } else {
                    geom.computeFaceNormals();
                }

                const mat = this.makeMaterial(object_json.color, object_json.opacity);

                if (object_json.opacity) {
                    mat.side = THREE.DoubleSide;  // not sure if this is necessary if we compute normals correctly
                    mat.transparent = true;
                    mat.depthWrite = false;
                }

                return obj;
            }
            case "convex": {
                return obj;
            }
            case "arrow": {
                return obj;
            }
            default: {
                return obj;
            }
        }

    }

    makeMaterial(color, opacity) {
        return new THREE.MeshStandardMaterial({
            color: color || '#52afb0',
            roughness: 0.1, metalness: 0.0,
            opacity: opacity || 1.0
        })
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

    static disposeNodebyName(scene, name) {
        let object = scene.getObjectByName(name);
        if (typeof object !== "undefined") {
            MP3D.disposeNode(object);
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

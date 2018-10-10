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
                sphere_segments: 32,
                reflections: false
            },
            other: {
                sphereScale: 1.0,
                cylinderScale: 1.0
            },
            lights: [
                {
                    type: 'DirectionalLight',
                    args: ["#ffffff", 0.003],
                    position: [-2, 2, 2]
                }
            ],
            material: {
                type: 'MeshStandardMaterial',
                parameters: {
                    roughness: 0.07,
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

        // Lights

        const ambientLight = new THREE.AmbientLight(0x222222, 0.015);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.05);
        directionalLight.position.set(-2, 2, 2);

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
        camera.add(ambientLight);
        camera.add(directionalLight);

        // Action

        const scene = new THREE.Scene();
        this.scene = scene;
        scene.add(camera);

        const root_obj = this.construct_root_obj(scene_json);
        scene.add(root_obj);

        const controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        controls.enableKeys = false;

        window.console.log(root_obj);

        dom_elt.appendChild(renderer.domElement);
        this.start();
    }

    construct_root_obj(scene_json) {

        const root_obj = new THREE.Object3D();
        root_obj.name = scene_json.name;

        function traverse_scene(o, parent, self) {
            o.contents.forEach(function (sub_o) {
                if (sub_o.hasOwnProperty('type')) {
                    parent.add(self.make_object(sub_o));
                } else {
                    let new_parent = new THREE.Object3D();
                    new_parent.name = sub_o.name;
                    parent.add(new_parent);
                    traverse_scene(sub_o, new_parent, self);
                }
            });
        }

        traverse_scene(scene_json, root_obj, this);

        return root_obj;

    }

    make_object(object_json) {

        const obj = new THREE.Object3D();
        obj.name = object_json.name;

        switch (object_json.type) {
            case "sphere":
                const geom = new THREE.SphereBufferGeometry(
                    object_json.radius,
                    this.settings.quality.sphere_segments,
                    this.settings.quality.sphere_segments,
                    object_json.phi_start || 0,
                    object_json.phi_end || Math.PI * 2
                );
                const mat = this.makeMaterial(object_json.color);
                object_json.positions.forEach(function(position) {
                    const mesh = new THREE.Mesh(geom, mat);
                    mesh.position.set(...position);
                    obj.add(mesh);
                });
                return obj;
            case "cylinder":
                break;
            case "lines":
                break;
            case "arrow":
                break;
            case "surface":
                break;
        }

    }

    makeMaterial(color) {
        return new THREE.MeshStandardMaterial({color: color, roughness: 0.1, metalness: 0.0})
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

}

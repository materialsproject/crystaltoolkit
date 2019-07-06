import * as THREE from "three-full";

export default class Simple3DScene {
  constructor(scene_json, dom_elt, settings) {
    this.start = this.start.bind(this);
    this.stop = this.stop.bind(this);
    this.animate = this.animate.bind(this);
    // var modifier = new THREE.SubdivisionModifier( 2 );


    const defaults = {
      shadows: true,
      antialias: true,
      transparent_background: true,
      sphereSegments: 32,
      cylinderSegments: 8,
      staticScene: true,
      sphereScale: 1.0,
      cylinderScale: 1.0,
      defaultSurfaceOpacity: 0.5,
      lights: [{ type: "HemisphereLight", args: ["#ffffff", "#202020", 1] }],
      material: {
        type: "MeshStandardMaterial",
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
      antialias: this.settings.antialias,
      alpha: this.settings.transparent_background,
      gammaInput: true,
      gammaOutput: true,
      gammaFactor: 2.2,
      shadowMapEnabled: this.settings.shadows,
      shadowMapType: THREE.PCFSoftShadowMap
    });
    this.renderer = renderer;

    renderer.setPixelRatio(
      window.devicePixelRatio
    );
    renderer.setClearColor(0xffffff, 0);
    renderer.setSize(width, height);
    dom_elt.appendChild(renderer.domElement);

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

    // Action

    this.addToScene(scene_json);

    // Lights

    const lights = this.makeLights(this.settings.lights);
    camera.add(lights);

    const controls = new THREE.OrbitControls(
      this.camera,
      this.renderer.domElement
    );
    controls.enableKeys = false;
    controls.minDistance = 1;
    controls.maxDistance = 250;
    controls.noPan = true;

    // initial render
    function render() {
      // TODO: brush up on JS! why can't we just use this.renderScene for EventListener?
      renderer.render(scene, camera);
    }
    render();

    if (this.settings.staticScene) {
      // only re-render when scene is rotated
      controls.addEventListener("change", render);
    } else {
      // constantly re-render (for animation)
      this.start();
    }

    function resizeRendererToDisplaySize() {
      const canvas = renderer.domElement;
      const width  = canvas.parentElement.clientWidth | 0;
      const height = canvas.parentElement.clientHeight | 0;
      if (canvas.width !== width || canvas.height !== height) {
        renderer.setSize(width, height, true);
      }
      renderer.render(scene, camera);
    }

    window.addEventListener( 'resize', resizeRendererToDisplaySize, false );
  }

  download(filename, filetype) {
    switch (filetype) {
      case "png":
        this.downloadScreenshot(filename);
        break;
    }
  }

  downloadScreenshot(filename) {
    // using method from Three.js editor

    // create a link and hide it from end-user
    var link = document.createElement("a");
    link.style.display = "none";
    document.body.appendChild(link);

    // force a render (in case buffer has been cleared)
    this.renderScene();
    // and set link href to renderer contents
    link.href = this.renderer.domElement.toDataURL("image/png");

    // click link to download
    link.download = filename || "screenshot.png";
    link.click();
  }

  addToScene(scene_json) {
    Simple3DScene.removeObjectByName(this.scene, scene_json.name);

    const root_obj = new THREE.Object3D();
    root_obj.name = scene_json.name;

    function traverse_scene(o, parent, self) {
      o.contents.forEach(function(sub_o) {
        if (sub_o.hasOwnProperty("type")) {
          parent.add(self.makeObject(sub_o));
        } else {
          const new_parent = new THREE.Object3D();
          new_parent.name = sub_o.name;
          parent.add(new_parent);
          traverse_scene(sub_o, new_parent, self);
        }
      });
    }

    traverse_scene(scene_json, root_obj, this);

    //window.console.log("root_obj", root_obj);

    this.scene.add(root_obj);

    // auto-zoom to fit object
    // TODO: maybe better to move this elsewhere (what if using perspective?)
    const box = new THREE.Box3();
    box.setFromObject(root_obj);
    const width = this.renderer.domElement.clientWidth;
    const height = this.renderer.domElement.clientHeight;
    // TODO: improve auto-zoom
    this.camera.zoom =
      Math.min(
        width / (box.max.x - box.min.x),
        height / (box.max.y - box.min.y)
      ) * 0.8;
    this.camera.updateProjectionMatrix();
    this.camera.updateMatrix();
    this.renderScene();
  }

  makeLights(light_json) {

    const lights = new THREE.Object3D();
    lights.name = "lights";

    light_json.forEach(function(light) {
      switch (light.type) {
        case "DirectionalLight":
          var lightObj = new THREE.DirectionalLight(...light.args);
          if (light.helper) {
            let lightHelper = new THREE.DirectionalLightHelper(
              lightObj,
              5,
              "#444444"
            );
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
      if (light.hasOwnProperty("position")) {
        lightObj.position.set(...light.position);
      }
      lights.add(lightObj);
    });

    return lights;
  }

  makeObject(object_json) {
    const obj = new THREE.Object3D();
    obj.name = object_json.name;

    if (object_json.visible) {
      obj.visible = object_json.visible;
    }

    switch (object_json.type) {
      case "spheres": {
        const geom = new THREE.SphereBufferGeometry(
          object_json.radius * this.settings.sphereScale,
          this.settings.sphereSegments,
          this.settings.sphereSegments,
          object_json.phiStart || 0,
          object_json.phiEnd || Math.PI * 2
        );
        const mat = this.makeMaterial(object_json.color);

        // if we allow occupancies not to sum to 100
        //if (object_json.phiStart || object_json.phiEnd) {
        //    mat.side = THREE.DoubleSide;
        //}

        const meshes = [];
        object_json.positions.forEach(function(position) {
          const mesh = new THREE.Mesh(geom, mat);
          mesh.position.set(...position);
          meshes.push(mesh);
        });

        // TODO: test axes are correct!
        if (object_json.ellipsoids) {
          const vec_z = new THREE.Vector3(0, 0, 1);
          const quaternion = new THREE.Quaternion();
          object_json.ellipsoids.rotations.forEach(function(rotation, index) {
            const rotation_vec = new THREE.Vector3(...rotation);
            quaternion.setFromUnitVectors(vec_z, rotation_vec.normalize());
            meshes[index].setRotationFromQuaternion(quaternion);
          });
          object_json.ellipsoids.scales.forEach(function(scale, index) {
            meshes[index].scale.set(...scale);
          });
        }

        meshes.forEach(function(mesh) {
          obj.add(mesh);
        });

        return obj;
      }
      case "cylinders": {
        const radius = object_json.radius || 1;

        const geom = new THREE.CylinderBufferGeometry(
          radius * this.settings.cylinderScale,
          radius * this.settings.cylinderScale,
          1.0,
          this.settings.cylinderSegments
        );
        const mat = this.makeMaterial(object_json.color);

        const vec_y = new THREE.Vector3(0, 1, 0); // initial axis of cylinder
        const quaternion = new THREE.Quaternion();

        object_json.positionPairs.forEach(function(positionPair) {
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
          quaternion.setFromUnitVectors(vec_y, vec_rel.normalize());
          mesh.setRotationFromQuaternion(quaternion);

          obj.add(mesh);
        });

        return obj;
      }
      case "cubes": {
        const geom = new THREE.BoxBufferGeometry(
          object_json.width * this.settings.sphereScale,
          object_json.width * this.settings.sphereScale,
          object_json.width * this.settings.sphereScale
        );
        const mat = this.makeMaterial(object_json.color);

        object_json.positions.forEach(function(position) {
          const mesh = new THREE.Mesh(geom, mat);
          mesh.position.set(...position);
          obj.add(mesh);
        });

        return obj;
      }
      case "lines": {
        const verts = new THREE.Float32BufferAttribute(
          [].concat.apply([], object_json.positions),
          3
        );
        const geom = new THREE.BufferGeometry();
        geom.addAttribute("position", verts);

        let mat;
        if (object_json.dashSize || object_json.scale || object_json.gapSize) {
          mat = new THREE.LineDashedMaterial({
            color: object_json.color || "#000000",
            linewidth: object_json.line_width || 1,
            scale: object_json.scale || 1,
            dashSize: object_json.dashSize || 3,
            gapSize: object_json.gapSize || 1
          });
        } else {
          mat = new THREE.LineBasicMaterial({
            color: object_json.color || "#2c3c54",
            linewidth: object_json.line_width || 1
          });
        }

        const mesh = new THREE.LineSegments(geom, mat);
        if (object_json.dashSize || object_json.scale || object_json.gapSize) {
          mesh.computeLineDistances();
        }
        obj.add(mesh);

        return obj;
      }
      case "surface": {
        const verts = new THREE.Float32BufferAttribute(
          [].concat.apply([], object_json.positions),
          3
        );
        const geom = new THREE.BufferGeometry();
        geom.addAttribute("position", verts);

        const opacity =
          object_json.opacity || this.settings.defaultSurfaceOpacity;
        const mat = this.makeMaterial(object_json.color, opacity);

        if (object_json.normals) {
          const normals = new THREE.Float32BufferAttribute(
            [].concat.apply([], object_json.normals),
            3
          );
          geom.addAttribute("normal", normals);
        } else {
          geom.computeFaceNormals();
          mat.side = THREE.DoubleSide; // not sure if this is necessary if we compute normals correctly
        }

        if (opacity) {
          mat.transparent = true;
          mat.depthWrite = false;
        }

        const mesh = new THREE.Mesh(geom, mat);
        obj.add(mesh);
        //TODO smooth the surfaces?
        return obj;
      }
      case "convex": {
        const points = object_json.positions.map(p => new THREE.Vector3(...p));
        const geom = new THREE.ConvexBufferGeometry(points);

        const opacity =
          object_json.opacity || this.settings.defaultSurfaceOpacity;
        const mat = this.makeMaterial(object_json.color, opacity);
        if (opacity) {
          mat.transparent = true;
          mat.depthWrite = false;
        }

        const mesh = new THREE.Mesh(geom, mat);
        obj.add(mesh);

        const edges = new THREE.EdgesGeometry(geom);
        const line = new THREE.LineSegments( edges, new THREE.LineBasicMaterial( { color: object_json.color } ) );
        obj.add(line);

        return obj;
      }
      case "arrows": {
        // take inspiration from ArrowHelper, user cones and cylinders
        const radius = object_json.radius || 1;
        const headLength = object_json.headLength || 2;
        const headWidth = object_json.headWidth || 2;

        // body
        const geom_cyl = new THREE.CylinderBufferGeometry(
          radius * this.settings.cylinderScale,
          radius * this.settings.cylinderScale,
          1.0,
          this.settings.cylinderSegments
        );
        // head
        const geom_head = new THREE.ConeBufferGeometry(
            headWidth* this.settings.cylinderScale,
            headLength* this.settings.cylinderScale,
            this.settings.cylinderSegments);

        const mat = this.makeMaterial(object_json.color);

        const vec_y = new THREE.Vector3(0, 1, 0); // initial axis of cylinder
        const vec_z = new THREE.Vector3(0, 0, 1); // initial axis of cylinder
        const quaternion = new THREE.Quaternion();
        const quaternion_head = new THREE.Quaternion();

        object_json.positionPairs.forEach(function(positionPair) {
          // the following is technically correct but could be optimized?

          const mesh = new THREE.Mesh(geom_cyl, mat);
          const vec_a = new THREE.Vector3(...positionPair[0]);
          const vec_b = new THREE.Vector3(...positionPair[1]);
          const vec_head = new THREE.Vector3(...positionPair[1]);
          const vec_rel = vec_b.sub(vec_a);

          // scale cylinder to correct length
          mesh.scale.y = vec_rel.length();

          // set origin at midpoint of cylinder
          const vec_midpoint = vec_a.add(vec_rel.clone().multiplyScalar(0.5));
          mesh.position.set(vec_midpoint.x, vec_midpoint.y, vec_midpoint.z);

          // rotate cylinder into correct orientation
          quaternion.setFromUnitVectors(vec_y, vec_rel.normalize());
          mesh.setRotationFromQuaternion(quaternion);

          obj.add(mesh);

          // add arrowhead
          const mesh_head = new THREE.Mesh(geom_head, mat);
          mesh_head.position.set(vec_head.x, vec_head.y, vec_head.z);
          // rotate cylinder into correct orientation
          quaternion_head.setFromUnitVectors(vec_y, vec_rel.normalize());
          mesh_head.setRotationFromQuaternion(quaternion_head);
          obj.add(mesh_head);
        });
        return obj;
      }
      case "labels": {
        // Not implemented
        //THREE.CSS2DObject see https://github.com/mrdoob/three.js/blob/master/examples/css2d_label.html
        return obj;
      }
      default: {
        return obj;
      }
    }
  }

  makeMaterial(color, opacity) {
    const parameters = Object.assign(this.settings.material.parameters, {
      color: color || "#52afb0",
      opacity: opacity || 1.0
    });

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
    if (typeof namesToVisibility !== "undefined") {
      for (var objName in namesToVisibility) {
        if (namesToVisibility.hasOwnProperty(objName)) {
          const obj = this.scene.getObjectByName(objName);
          if (typeof obj !== "undefined") {
            obj.visible = Boolean(namesToVisibility[objName]);
          }
        }
      }
    }
    this.renderScene();
  }

  static removeObjectByName(scene, name) {
    // name is not necessarily unique, make this recursive ?
    const object = scene.getObjectByName(name);
    if (typeof object !== "undefined") {
        scene.remove(object);
    }
  }

}

import * as THREE from "three-full";
//import JSZip from "jszip";

export default class Simple3DScene {
  constructor(scene_json, dom_elt, settings) {
    this.start = this.start.bind(this);
    this.stop = this.stop.bind(this);
    this.animate = this.animate.bind(this);

    const defaults = {
      shadows: true,
      antialias: true,
      transparent_background: true,
      pixelRatio: 1.5,
      sphereSegments: 32,
      cylinderSegments: 8,
      reflections: false,
      staticScene: true,
      autorotate: true,
      objectScale: 1.0,
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

    console.log(window.devicePixelRatio);
    renderer.setPixelRatio(
      window.devicePixelRatio // * this.settings.pixelRatio
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

    this.makeLights(scene, this.settings.lights);

    const controls = new THREE.OrbitControls(
      this.camera,
      this.renderer.domElement
    );
    controls.enableKeys = false;

    // initial render
    function render() {
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

    // allow resize
    //function onWindowResize(){
    //    // not implemented
    //}
    //window.addEventListener( 'resize', onWindowResize, false );
  }

  download(filename, filetype) {
    switch (filetype) {
      case "png":
        this.downloadScreenshot(filename);
        break;
      case "dae":
        this.downloadCollada(filename);
        break;
    }
  }

  downloadCollada(filename) {

    // Do not use yet. Adapted from ColladaArchiveExporter from @gkjohnson

    const files = new THREE.ColladaExporter().parse(this.scene);
    const manifest =
      '<?xml version="1.0" encoding="utf-8"?>' +
      `<dae_root>./${filename}</dae_root>`;

    const zip = new JSZip();
    zip.file("manifest.xml", manifest);
    zip.file(filename, files.data);
    files.textures.forEach(tex =>
      zip.file(`${tex.directory}${tex.name}.${tex.ext}`, tex.data)
    );

    var link = document.createElement("a");
    //link.style.display = "none";
    document.body.appendChild(link);
    zip.generateAsync({ type: "base64" }).then(function(base64) {
      link.href = "data:application/zip;base64," + base64;
    });
    link.download = filename || "scene.dae";
    //link.click();
  }

  downloadGLTF(filename) {
    // Not Implemented Yet
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
    Simple3DScene.disposeNodebyName(this.scene, scene_json.name);

    const root_obj = new THREE.Object3D();
    root_obj.name = scene_json.name;

    function traverse_scene(o, parent, self) {
      o.contents.forEach(function(sub_o) {
        if (sub_o.hasOwnProperty("type")) {
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

    // window.console.log(root_obj);

    this.scene.add(root_obj);

    // auto-zoom to fit object
    // TODO: maybe better to move this elsewhere (what if using perspective?)
    const box = new THREE.Box3();
    box.setFromObject(root_obj);
    const width = this.renderer.domElement.clientWidth;
    const height = this.renderer.domElement.clientHeight;
    this.camera.zoom =
      Math.min(
        width / (box.max.x - box.min.x),
        height / (box.max.y - box.min.y)
      ) * 0.5;
    this.camera.updateProjectionMatrix();
    this.camera.updateMatrix();
  }

  makeLights(scene, light_json) {
    Simple3DScene.disposeNodebyName(scene, "lights");

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

    // window.console.log("lights", lights);

    scene.add(lights);
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
          object_json.radius * this.settings.objectScale,
          this.settings.sphereSegments,
          this.settings.sphereSegments,
          object_json.phiStart || 0,
          object_json.phiEnd || Math.PI * 2
        );
        const mat = this.makeMaterial(object_json.color);

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
          object_json.width * this.settings.objectScale,
          object_json.width * this.settings.objectScale,
          object_json.width * this.settings.objectScale
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

        return obj;
      }
      case "arrows": {
        // take inspiration from ArrowHelper, user cones and cylinders
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
    // for names in namesToVisibility ... if 1, show, if 0 hide
    if (typeof namesToVisibility !== "undefined") {
      for (var objName in namesToVisibility) {
        if (namesToVisibility.hasOwnProperty(objName)) {
          const obj = this.scene.getObjectByName(objName);
          if (typeof obj !== "undefined") {
            obj.visible = Boolean(namesToVisibility.objName);
          }
        }
      }
    }
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
    parentObject.traverse(function(node) {
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
            materialArray.forEach(function(mtrl, idx) {
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

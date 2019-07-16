define(["exports", "three-full"], function (exports, _threeFull) {
  "use strict";

  Object.defineProperty(exports, "__esModule", {
    value: true
  });

  var THREE = _interopRequireWildcard(_threeFull);

  function _interopRequireWildcard(obj) {
    if (obj && obj.__esModule) {
      return obj;
    } else {
      var newObj = {};

      if (obj != null) {
        for (var key in obj) {
          if (Object.prototype.hasOwnProperty.call(obj, key)) newObj[key] = obj[key];
        }
      }

      newObj.default = obj;
      return newObj;
    }
  }

  function _toConsumableArray(arr) {
    if (Array.isArray(arr)) {
      for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) {
        arr2[i] = arr[i];
      }

      return arr2;
    } else {
      return Array.from(arr);
    }
  }

  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError("Cannot call a class as a function");
    }
  }

  var _createClass = function () {
    function defineProperties(target, props) {
      for (var i = 0; i < props.length; i++) {
        var descriptor = props[i];
        descriptor.enumerable = descriptor.enumerable || false;
        descriptor.configurable = true;
        if ("value" in descriptor) descriptor.writable = true;
        Object.defineProperty(target, descriptor.key, descriptor);
      }
    }

    return function (Constructor, protoProps, staticProps) {
      if (protoProps) defineProperties(Constructor.prototype, protoProps);
      if (staticProps) defineProperties(Constructor, staticProps);
      return Constructor;
    };
  }();

  var Simple3DScene = function () {
    function Simple3DScene(scene_json, dom_elt, settings) {
      _classCallCheck(this, Simple3DScene);

      this.start = this.start.bind(this);
      this.stop = this.stop.bind(this);
      this.animate = this.animate.bind(this);
      // var modifier = new THREE.SubdivisionModifier( 2 );


      var defaults = {
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
        },
        enableZoom: true,
        defaultZoom: 0.8
      };

      this.settings = Object.assign(defaults, settings);

      // Stage

      var width = dom_elt.clientWidth;
      var height = dom_elt.clientHeight;

      var renderer = new THREE.WebGLRenderer({
        antialias: this.settings.antialias,
        alpha: this.settings.transparent_background,
        gammaInput: true,
        gammaOutput: true,
        gammaFactor: 2.2,
        shadowMapEnabled: this.settings.shadows,
        shadowMapType: THREE.PCFSoftShadowMap
      });
      this.renderer = renderer;

      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setClearColor(0xffffff, 0);
      renderer.setSize(width, height);
      dom_elt.appendChild(renderer.domElement);

      var scene = new THREE.Scene();
      this.scene = scene;

      // Camera

      // TODO: change so camera dimensions match scene, not dom_elt?
      var camera = new THREE.OrthographicCamera(width / -2, width / 2, height / 2, height / -2, -2000, 2000);
      // need to offset for OrbitControls
      camera.position.z = 2;

      this.camera = camera;
      scene.add(camera);

      // Action

      this.addToScene(scene_json);

      // Lights

      var lights = this.makeLights(this.settings.lights);
      camera.add(lights);

      var controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      controls.enableKeys = false;
      controls.minZoom = 2;
      controls.maxZoom = 100;
      controls.enablePan = false;
      controls.enableZoom = this.settings.enableZoom;

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
        var canvas = renderer.domElement;
        var width = canvas.parentElement.clientWidth | 0;
        var height = canvas.parentElement.clientHeight | 0;
        if (canvas.width !== width || canvas.height !== height) {
          renderer.setSize(width, height, true);
        }
        renderer.render(scene, camera);
      }

      window.addEventListener('resize', resizeRendererToDisplaySize, false);
    }

    _createClass(Simple3DScene, [{
      key: "download",
      value: function download(filename, filetype) {
        switch (filetype) {
          case "png":
            this.downloadScreenshot(filename);
            break;
          default:
            throw new Error("Unknown filetype.");
        }
      }
    }, {
      key: "downloadScreenshot",
      value: function downloadScreenshot(filename) {
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
    }, {
      key: "addToScene",
      value: function addToScene(scene_json) {
        Simple3DScene.removeObjectByName(this.scene, scene_json.name);

        var root_obj = new THREE.Object3D();
        root_obj.name = scene_json.name;

        function traverse_scene(o, parent, self) {
          o.contents.forEach(function (sub_o) {
            if (sub_o.hasOwnProperty("type")) {
              parent.add(self.makeObject(sub_o));
            } else {
              var new_parent = new THREE.Object3D();
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
        var box = new THREE.Box3();
        box.setFromObject(root_obj);
        var width = this.renderer.domElement.clientWidth;
        var height = this.renderer.domElement.clientHeight;
        // TODO: improve auto-zoom
        this.camera.zoom = Math.min(Math.max(width, height) / (box.max.x - box.min.x), Math.max(width, height) / (box.max.y - box.min.y), Math.max(width, height) / (box.max.z - box.min.z)) * this.settings.defaultZoom;
        this.camera.updateProjectionMatrix();
        this.camera.updateMatrix();
        this.renderScene();
      }
    }, {
      key: "makeLights",
      value: function makeLights(light_json) {

        var lights = new THREE.Object3D();
        lights.name = "lights";

        light_json.forEach(function (light) {
          switch (light.type) {
            case "DirectionalLight":
              var lightObj = new (Function.prototype.bind.apply(THREE.DirectionalLight, [null].concat(_toConsumableArray(light.args))))();
              if (light.helper) {
                var lightHelper = new THREE.DirectionalLightHelper(lightObj, 5, "#444444");
                lightObj.add(lightHelper);
              }
              break;
            case "AmbientLight":
              var lightObj = new (Function.prototype.bind.apply(THREE.AmbientLight, [null].concat(_toConsumableArray(light.args))))();
              break;
            case "HemisphereLight":
              var lightObj = new (Function.prototype.bind.apply(THREE.HemisphereLight, [null].concat(_toConsumableArray(light.args))))();
              break;
            default:
              throw new Error("Unknown light.");
          }
          if (light.hasOwnProperty("position")) {
            var _lightObj$position;

            (_lightObj$position = lightObj.position).set.apply(_lightObj$position, _toConsumableArray(light.position));
          }
          lights.add(lightObj);
        });

        return lights;
      }
    }, {
      key: "makeObject",
      value: function makeObject(object_json) {
        var obj = new THREE.Object3D();
        obj.name = object_json.name;

        if (object_json.visible) {
          obj.visible = object_json.visible;
        }

        switch (object_json.type) {
          case "spheres":
            {
              var geom = new THREE.SphereBufferGeometry(object_json.radius * this.settings.sphereScale, this.settings.sphereSegments, this.settings.sphereSegments, object_json.phiStart || 0, object_json.phiEnd || Math.PI * 2);
              var mat = this.makeMaterial(object_json.color);

              // if we allow occupancies not to sum to 100
              //if (object_json.phiStart || object_json.phiEnd) {
              //    mat.side = THREE.DoubleSide;
              //}

              var meshes = [];
              object_json.positions.forEach(function (position) {
                var _mesh$position;

                var mesh = new THREE.Mesh(geom, mat);
                (_mesh$position = mesh.position).set.apply(_mesh$position, _toConsumableArray(position));
                meshes.push(mesh);
              });

              // TODO: test axes are correct!
              if (object_json.ellipsoids) {
                var vec_z = new THREE.Vector3(0, 0, 1);
                var quaternion = new THREE.Quaternion();
                object_json.ellipsoids.rotations.forEach(function (rotation, index) {
                  var rotation_vec = new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(rotation))))();
                  quaternion.setFromUnitVectors(vec_z, rotation_vec.normalize());
                  meshes[index].setRotationFromQuaternion(quaternion);
                });
                object_json.ellipsoids.scales.forEach(function (scale, index) {
                  var _meshes$index$scale;

                  (_meshes$index$scale = meshes[index].scale).set.apply(_meshes$index$scale, _toConsumableArray(scale));
                });
              }

              meshes.forEach(function (mesh) {
                obj.add(mesh);
              });

              return obj;
            }
          case "cylinders":
            {
              var radius = object_json.radius || 1;

              var _geom = new THREE.CylinderBufferGeometry(radius * this.settings.cylinderScale, radius * this.settings.cylinderScale, 1.0, this.settings.cylinderSegments);
              var _mat = this.makeMaterial(object_json.color);

              var vec_y = new THREE.Vector3(0, 1, 0); // initial axis of cylinder
              var _quaternion = new THREE.Quaternion();

              object_json.positionPairs.forEach(function (positionPair) {
                // the following is technically correct but could be optimized?

                var mesh = new THREE.Mesh(_geom, _mat);
                var vec_a = new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(positionPair[0]))))();
                var vec_b = new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(positionPair[1]))))();
                var vec_rel = vec_b.sub(vec_a);

                // scale cylinder to correct length
                mesh.scale.y = vec_rel.length();

                // set origin at midpoint of cylinder
                var vec_midpoint = vec_a.add(vec_rel.clone().multiplyScalar(0.5));
                mesh.position.set(vec_midpoint.x, vec_midpoint.y, vec_midpoint.z);

                // rotate cylinder into correct orientation
                _quaternion.setFromUnitVectors(vec_y, vec_rel.normalize());
                mesh.setRotationFromQuaternion(_quaternion);

                obj.add(mesh);
              });

              return obj;
            }
          case "cubes":
            {
              var _geom2 = new THREE.BoxBufferGeometry(object_json.width * this.settings.sphereScale, object_json.width * this.settings.sphereScale, object_json.width * this.settings.sphereScale);
              var _mat2 = this.makeMaterial(object_json.color);

              object_json.positions.forEach(function (position) {
                var _mesh$position2;

                var mesh = new THREE.Mesh(_geom2, _mat2);
                (_mesh$position2 = mesh.position).set.apply(_mesh$position2, _toConsumableArray(position));
                obj.add(mesh);
              });

              return obj;
            }
          case "lines":
            {
              var verts = new THREE.Float32BufferAttribute([].concat.apply([], object_json.positions), 3);
              var _geom3 = new THREE.BufferGeometry();
              _geom3.addAttribute("position", verts);

              var _mat3 = void 0;
              if (object_json.dashSize || object_json.scale || object_json.gapSize) {
                _mat3 = new THREE.LineDashedMaterial({
                  color: object_json.color || "#000000",
                  linewidth: object_json.line_width || 1,
                  scale: object_json.scale || 1,
                  dashSize: object_json.dashSize || 3,
                  gapSize: object_json.gapSize || 1
                });
              } else {
                _mat3 = new THREE.LineBasicMaterial({
                  color: object_json.color || "#2c3c54",
                  linewidth: object_json.line_width || 1
                });
              }

              var mesh = new THREE.LineSegments(_geom3, _mat3);
              if (object_json.dashSize || object_json.scale || object_json.gapSize) {
                mesh.computeLineDistances();
              }
              obj.add(mesh);

              return obj;
            }
          case "surface":
            {
              var _verts = new THREE.Float32BufferAttribute([].concat.apply([], object_json.positions), 3);
              var _geom4 = new THREE.BufferGeometry();
              _geom4.addAttribute("position", _verts);

              var opacity = object_json.opacity || this.settings.defaultSurfaceOpacity;
              var _mat4 = this.makeMaterial(object_json.color, opacity);

              if (object_json.normals) {
                var normals = new THREE.Float32BufferAttribute([].concat.apply([], object_json.normals), 3);
                _geom4.addAttribute("normal", normals);
              } else {
                _geom4.computeFaceNormals();
                _mat4.side = THREE.DoubleSide; // not sure if this is necessary if we compute normals correctly
              }

              if (opacity) {
                _mat4.transparent = true;
                _mat4.depthWrite = false;
              }

              var _mesh = new THREE.Mesh(_geom4, _mat4);
              obj.add(_mesh);
              //TODO smooth the surfaces?
              return obj;
            }
          case "convex":
            {
              var points = object_json.positions.map(function (p) {
                return new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(p))))();
              });
              var _geom5 = new THREE.ConvexBufferGeometry(points);

              var _opacity = object_json.opacity || this.settings.defaultSurfaceOpacity;
              var _mat5 = this.makeMaterial(object_json.color, _opacity);
              if (_opacity) {
                _mat5.transparent = true;
                _mat5.depthWrite = false;
              }

              var _mesh2 = new THREE.Mesh(_geom5, _mat5);
              obj.add(_mesh2);

              var edges = new THREE.EdgesGeometry(_geom5);
              var line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: object_json.color }));
              obj.add(line);

              return obj;
            }
          case "arrows":
            {
              // take inspiration from ArrowHelper, user cones and cylinders
              var _radius = object_json.radius || 1;
              var headLength = object_json.headLength || 2;
              var headWidth = object_json.headWidth || 2;

              // body
              var geom_cyl = new THREE.CylinderBufferGeometry(_radius * this.settings.cylinderScale, _radius * this.settings.cylinderScale, 1.0, this.settings.cylinderSegments);
              // head
              var geom_head = new THREE.ConeBufferGeometry(headWidth * this.settings.cylinderScale, headLength * this.settings.cylinderScale, this.settings.cylinderSegments);

              var _mat6 = this.makeMaterial(object_json.color);

              var _vec_y = new THREE.Vector3(0, 1, 0); // initial axis of cylinder
              var _vec_z = new THREE.Vector3(0, 0, 1); // initial axis of cylinder
              var _quaternion2 = new THREE.Quaternion();
              var quaternion_head = new THREE.Quaternion();

              object_json.positionPairs.forEach(function (positionPair) {
                // the following is technically correct but could be optimized?

                var mesh = new THREE.Mesh(geom_cyl, _mat6);
                var vec_a = new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(positionPair[0]))))();
                var vec_b = new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(positionPair[1]))))();
                var vec_head = new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(positionPair[1]))))();
                var vec_rel = vec_b.sub(vec_a);

                // scale cylinder to correct length
                mesh.scale.y = vec_rel.length();

                // set origin at midpoint of cylinder
                var vec_midpoint = vec_a.add(vec_rel.clone().multiplyScalar(0.5));
                mesh.position.set(vec_midpoint.x, vec_midpoint.y, vec_midpoint.z);

                // rotate cylinder into correct orientation
                _quaternion2.setFromUnitVectors(_vec_y, vec_rel.normalize());
                mesh.setRotationFromQuaternion(_quaternion2);

                obj.add(mesh);

                // add arrowhead
                var mesh_head = new THREE.Mesh(geom_head, _mat6);
                mesh_head.position.set(vec_head.x, vec_head.y, vec_head.z);
                // rotate cylinder into correct orientation
                quaternion_head.setFromUnitVectors(_vec_y, vec_rel.normalize());
                mesh_head.setRotationFromQuaternion(quaternion_head);
                obj.add(mesh_head);
              });
              return obj;
            }
          case "labels":
            {
              // Not implemented
              //THREE.CSS2DObject see https://github.com/mrdoob/three.js/blob/master/examples/css2d_label.html
              return obj;
            }
          default:
            {
              return obj;
            }
        }
      }
    }, {
      key: "makeMaterial",
      value: function makeMaterial(color, opacity) {
        var parameters = Object.assign(this.settings.material.parameters, {
          color: color || "#52afb0",
          opacity: opacity || 1.0
        });

        switch (this.settings.material.type) {
          case "MeshStandardMaterial":
            {
              return new THREE.MeshStandardMaterial(parameters);
            }
          default:
            throw new Error("Unknown material.");
        }
      }
    }, {
      key: "start",
      value: function start() {
        if (!this.frameId) {
          this.frameId = requestAnimationFrame(this.animate);
        }
      }
    }, {
      key: "stop",
      value: function stop() {
        cancelAnimationFrame(this.frameId);
      }
    }, {
      key: "animate",
      value: function animate() {
        this.renderScene();
        this.frameId = window.requestAnimationFrame(this.animate);
      }
    }, {
      key: "renderScene",
      value: function renderScene() {
        this.renderer.render(this.scene, this.camera);
      }
    }, {
      key: "toggleVisibility",
      value: function toggleVisibility(namesToVisibility) {
        if (typeof namesToVisibility !== "undefined") {
          for (var objName in namesToVisibility) {
            if (namesToVisibility.hasOwnProperty(objName)) {
              var obj = this.scene.getObjectByName(objName);
              if (typeof obj !== "undefined") {
                obj.visible = Boolean(namesToVisibility[objName]);
              }
            }
          }
        }
        this.renderScene();
      }
    }], [{
      key: "removeObjectByName",
      value: function removeObjectByName(scene, name) {
        // name is not necessarily unique, make this recursive ?
        var object = scene.getObjectByName(name);
        if (typeof object !== "undefined") {
          scene.remove(object);
        }
      }
    }]);

    return Simple3DScene;
  }();

  exports.default = Simple3DScene;
});


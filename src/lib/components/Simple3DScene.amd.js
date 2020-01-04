define(['exports', 'three', '../../../node_modules/three/examples/jsm/controls/TrackballControls.js', '../../../node_modules/three/examples/jsm/geometries/ConvexGeometry.js', '../../../node_modules/three/examples/jsm/renderers/CSS2DRenderer.js', '../../../node_modules/three/examples/jsm/renderers/SVGRenderer.js', '../../../node_modules/three/examples/jsm/exporters/ColladaExporter', 'jszip'], function (exports, _three, _TrackballControls, _ConvexGeometry, _CSS2DRenderer, _SVGRenderer, _ColladaExporter, _jszip) {
  'use strict';

  Object.defineProperty(exports, "__esModule", {
    value: true
  });

  var THREE = _interopRequireWildcard(_three);

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

      var defaults = {
        antialias: true,
        transparentBackground: false,
        renderer: 'webgl',
        renderDivBackground: false,
        background: '#ffffff',
        sphereSegments: 32,
        cylinderSegments: 16,
        staticScene: true,
        sphereScale: 1.0,
        cylinderScale: 1.0,
        defaultSurfaceOpacity: 0.5,
        lights: [{
          type: 'HemisphereLight',
          args: ['#eeeeee', '#999999', 1.0]
        }, {
          type: 'DirectionalLight',
          args: ['#ffffff', 0.15],
          position: [0, 0, -10]
        }, {
          type: 'DirectionalLight',
          args: ['#ffffff', 0.15],
          position: [-10, 10, 10]
        }],
        material: {
          type: 'MeshStandardMaterial',
          parameters: {
            roughness: 0.07,
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

      var renderer = void 0;
      if (this.settings.renderer === 'webgl') {
        renderer = new THREE.WebGLRenderer({
          antialias: this.settings.antialias,
          alpha: this.settings.transparentBackground,
          gammaInput: true,
          gammaOutput: true,
          gammaFactor: 2.2
        });
      } else if (this.settings.renderer === 'svg') {
        renderer = new _SVGRenderer.SVGRenderer();
      }

      this.renderer = renderer;

      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setSize(width, height);
      dom_elt.appendChild(renderer.domElement);

      var labelRenderer = new _CSS2DRenderer.CSS2DRenderer();
      this.labelRenderer = labelRenderer;
      labelRenderer.setSize(width, height);
      labelRenderer.domElement.style.position = 'relative';
      labelRenderer.domElement.style.top = '-' + height + 'px';
      labelRenderer.domElement.style.pointerEvents = 'none';
      dom_elt.appendChild(labelRenderer.domElement);

      var scene = new THREE.Scene();
      if (!this.settings.transparentBackground) {
        scene.background = new THREE.Color(this.settings.background);
      }
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

      var controls = new _TrackballControls.TrackballControls(this.camera, this.renderer.domElement);
      controls.enableKeys = false;

      // for OrbitControls
      //controls.minDistance = 20
      //controls.maxDistance = 50
      //controls.noPan = true
      //controls.noZoom = !this.settings.enableZoom
      //controls.rotateSpeed = 4.0
      //controls.zoomSpeed = 2.0
      //controls.staticMoving = true

      // initial render
      function render() {
        // TODO: brush up on JS! why can't we just use this.renderScene for EventListener?
        renderer.render(scene, camera);
        labelRenderer.render(scene, camera);
      }
      render();

      if (this.settings.staticScene) {
        // only re-render when scene is rotated
        controls.addEventListener('change', render);
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
          labelRenderer.setSize(width, height);
        }
        renderer.render(scene, camera);
        labelRenderer.render(scene, camera);
      }

      window.addEventListener('resize', resizeRendererToDisplaySize, false);

      // clickable object reference
      this.clickable_objects = [];
    }

    _createClass(Simple3DScene, [{
      key: 'download',
      value: function download(filename, filetype) {
        switch (filetype) {
          case 'png':
            this.downloadScreenshot(filename);
            break;
          case 'dae':
            this.downloadCollada(filename);
            break;
          default:
            throw new Error('Unknown filetype.');
        }
      }
    }, {
      key: 'downloadScreenshot',
      value: function downloadScreenshot(filename) {
        // using method from Three.js editor

        // create a link and hide it from end-user
        var link = document.createElement('a');
        link.style.display = 'none';
        document.body.appendChild(link);

        // force a render (in case buffer has been cleared)
        this.renderScene();
        // and set link href to renderer contents
        link.href = this.renderer.domElement.toDataURL('image/png');

        // click link to download
        link.download = filename || 'screenshot.png';
        link.click();
      }
    }, {
      key: 'downloadCollada',
      value: function downloadCollada(filename) {
        // Adapted from ColladaArchiveExporter from @gkjohnson

        var files = new _ColladaExporter.ColladaExporter().parse(this.scene);
        var manifest = '<?xml version="1.0" encoding="utf-8"?>' + ('<dae_root>./' + filename + '</dae_root>');

        var zip = new _jszip.JSZip();
        zip.file("manifest.xml", manifest);
        zip.file(filename, files.data);
        files.textures.forEach(function (tex) {
          return zip.file('' + tex.directory + tex.name + '.' + tex.ext, tex.data);
        });

        var link = document.createElement("a");
        link.style.display = "none";
        document.body.appendChild(link);
        zip.generateAsync({ type: "base64" }).then(function (base64) {
          link.href = "data:application/zip;base64," + base64;
        });
        link.download = filename || "scene.dae";
        link.click();
      }
    }, {
      key: 'addToScene',
      value: function addToScene(scene_json) {
        Simple3DScene.removeObjectByName(this.scene, scene_json.name);
        this.clickable_objects = [];

        var root_obj = new THREE.Object3D();
        root_obj.name = scene_json.name;

        function traverse_scene(o, parent, self) {
          o.contents.forEach(function (sub_o) {
            if (sub_o.hasOwnProperty('type')) {
              parent.add(self.makeObject(sub_o));
            } else {
              var new_parent = new THREE.Object3D();
              new_parent.name = sub_o.name;
              if (sub_o.hasOwnProperty("origin")) {
                var translation = new THREE.Matrix4();
                translation.makeTranslation.apply(translation, _toConsumableArray(sub_o.origin));
                new_parent.applyMatrix(translation);
              }
              parent.add(new_parent);
              traverse_scene(sub_o, new_parent, self);
            }
          });
        }

        traverse_scene(scene_json, root_obj, this);

        // window.console.log("root_obj", root_obj);

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

        // we can automatically output a screenshot to be the background of the parent div
        // this helps for automated testing, printing the web page, etc.
        if (this.settings.renderDivBackground) {
          this.renderer.domElement.parentElement.style.backgroundSize = '100%';
          this.renderer.domElement.parentElement.style.backgroundRepeat = 'no-repeat';
          this.renderer.domElement.parentElement.style.backgroundPosition = 'center';
          this.renderer.domElement.parentElement.style.backgroundImage = "url('" + this.renderer.domElement.toDataURL('image/png') + "')";
        }
      }
    }, {
      key: 'makeLights',
      value: function makeLights(light_json) {
        var lights = new THREE.Object3D();
        lights.name = 'lights';

        light_json.forEach(function (light) {
          switch (light.type) {
            case 'DirectionalLight':
              var lightObj = new (Function.prototype.bind.apply(THREE.DirectionalLight, [null].concat(_toConsumableArray(light.args))))();
              if (light.helper) {
                var lightHelper = new THREE.DirectionalLightHelper(lightObj, 5, '#444444');
                lightObj.add(lightHelper);
              }
              break;
            case 'AmbientLight':
              var lightObj = new (Function.prototype.bind.apply(THREE.AmbientLight, [null].concat(_toConsumableArray(light.args))))();
              break;
            case 'HemisphereLight':
              var lightObj = new (Function.prototype.bind.apply(THREE.HemisphereLight, [null].concat(_toConsumableArray(light.args))))();
              break;
            default:
              throw new Error('Unknown light.');
          }
          if (light.hasOwnProperty('position')) {
            var _lightObj$position;

            (_lightObj$position = lightObj.position).set.apply(_lightObj$position, _toConsumableArray(light.position));
          }
          lights.add(lightObj);
        });

        return lights;
      }
    }, {
      key: 'makeObject',
      value: function makeObject(object_json) {
        var obj = new THREE.Object3D();
        obj.name = object_json.name;

        if (object_json.visible) {
          obj.visible = object_json.visible;
        }

        if (object_json.clickable) {
          obj.reference = object_json.reference;
          this.clickable_objects.push(obj);
        };

        switch (object_json.type) {
          case 'spheres':
            {
              var geom = new THREE.SphereBufferGeometry(object_json.radius * this.settings.sphereScale, this.settings.sphereSegments, this.settings.sphereSegments, object_json.phiStart || 0, object_json.phiEnd || Math.PI * 2);
              var mat = this.makeMaterial(object_json.color);

              // if we allow occupancies not to sum to 100
              // if (object_json.phiStart || object_json.phiEnd) {
              //    mat.side = THREE.DoubleSide;
              // }

              var meshes = [];
              object_json.positions.forEach(function (position) {
                var _mesh$position;

                var mesh = new THREE.Mesh(geom, mat);
                (_mesh$position = mesh.position).set.apply(_mesh$position, _toConsumableArray(position));
                meshes.push(mesh);
              });

              meshes.forEach(function (mesh) {
                obj.add(mesh);
              });

              return obj;
            }
          case 'ellipsoids':
            {
              var _geom = new THREE.SphereBufferGeometry(this.settings.sphereScale, this.settings.sphereSegments, this.settings.sphereSegments, object_json.phiStart || 0, object_json.phiEnd || Math.PI * 2);
              var _mat = this.makeMaterial(object_json.color);

              // if we allow occupancies not to sum to 100
              // if (object_json.phiStart || object_json.phiEnd) {
              //    mat.side = THREE.DoubleSide;
              // }

              var _meshes = [];
              object_json.positions.forEach(function (position) {
                var _mesh$position2, _mesh$scale;

                var mesh = new THREE.Mesh(_geom, _mat);
                (_mesh$position2 = mesh.position).set.apply(_mesh$position2, _toConsumableArray(position));
                (_mesh$scale = mesh.scale).set.apply(_mesh$scale, _toConsumableArray(object_json.scale)); // TODO: Is this valid JS?
                _meshes.push(mesh);
              });

              // TODO: test axes are correct!

              var vec_z = new THREE.Vector3(0, 0, 1);
              var quaternion = new THREE.Quaternion();
              object_json.rotate_to.forEach(function (rotation, index) {
                var rotation_vec = new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(rotation))))();
                quaternion.setFromUnitVectors(vec_z, rotation_vec.normalize());
                _meshes[index].setRotationFromQuaternion(quaternion);
              });

              _meshes.forEach(function (mesh) {
                obj.add(mesh);
              });

              return obj;
            }
          case 'cylinders':
            {
              var radius = object_json.radius || 1;

              var _geom2 = new THREE.CylinderBufferGeometry(radius * this.settings.cylinderScale, radius * this.settings.cylinderScale, 1.0, this.settings.cylinderSegments);
              var _mat2 = this.makeMaterial(object_json.color);

              var vec_y = new THREE.Vector3(0, 1, 0); // initial axis of cylinder
              var _quaternion = new THREE.Quaternion();

              object_json.positionPairs.forEach(function (positionPair) {
                // the following is technically correct but could be optimized?

                var mesh = new THREE.Mesh(_geom2, _mat2);
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
          case 'cubes':
            {
              var _geom3 = new THREE.BoxBufferGeometry(object_json.width * this.settings.sphereScale, object_json.width * this.settings.sphereScale, object_json.width * this.settings.sphereScale);
              var _mat3 = this.makeMaterial(object_json.color);

              object_json.positions.forEach(function (position) {
                var _mesh$position3;

                var mesh = new THREE.Mesh(_geom3, _mat3);
                (_mesh$position3 = mesh.position).set.apply(_mesh$position3, _toConsumableArray(position));
                obj.add(mesh);
              });

              return obj;
            }
          case 'lines':
            {
              var verts = new THREE.Float32BufferAttribute([].concat.apply([], object_json.positions), 3);
              var _geom4 = new THREE.BufferGeometry();
              _geom4.addAttribute('position', verts);

              var _mat4 = void 0;
              if (object_json.dashSize || object_json.scale || object_json.gapSize) {
                _mat4 = new THREE.LineDashedMaterial({
                  color: object_json.color || '#000000',
                  linewidth: object_json.line_width || 1,
                  scale: object_json.scale || 1,
                  dashSize: object_json.dashSize || 3,
                  gapSize: object_json.gapSize || 1
                });
              } else {
                _mat4 = new THREE.LineBasicMaterial({
                  color: object_json.color || '#2c3c54',
                  linewidth: object_json.line_width || 1
                });
              }

              var mesh = new THREE.LineSegments(_geom4, _mat4);
              if (object_json.dashSize || object_json.scale || object_json.gapSize) {
                mesh.computeLineDistances();
              }
              obj.add(mesh);

              return obj;
            }
          case 'surface':
            {
              var _verts = new THREE.Float32BufferAttribute([].concat.apply([], object_json.positions), 3);
              var _geom5 = new THREE.BufferGeometry();
              _geom5.addAttribute('position', _verts);

              var opacity = object_json.opacity || this.settings.defaultSurfaceOpacity;
              var _mat5 = this.makeMaterial(object_json.color, opacity);

              if (object_json.normals) {
                var normals = new THREE.Float32BufferAttribute([].concat.apply([], object_json.normals), 3);
                _geom5.addAttribute('normal', normals);
              } else {
                _geom5.computeFaceNormals();
                _mat5.side = THREE.DoubleSide; // not sure if this is necessary if we compute normals correctly
              }

              if (opacity) {
                _mat5.transparent = true;
                _mat5.depthWrite = false;
              }

              var _mesh = new THREE.Mesh(_geom5, _mat5);
              obj.add(_mesh);
              // TODO: smooth the surfaces?
              return obj;
            }
          case 'convex':
            {
              var points = object_json.positions.map(function (p) {
                return new (Function.prototype.bind.apply(THREE.Vector3, [null].concat(_toConsumableArray(p))))();
              });
              var _geom6 = new _ConvexGeometry.ConvexBufferGeometry(points);

              var _opacity = object_json.opacity || this.settings.defaultSurfaceOpacity;
              var _mat6 = this.makeMaterial(object_json.color, _opacity);
              if (_opacity) {
                _mat6.transparent = true;
                _mat6.depthWrite = false;
              }

              var _mesh2 = new THREE.Mesh(_geom6, _mat6);
              obj.add(_mesh2);

              var edges = new THREE.EdgesGeometry(_geom6);
              var line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: object_json.color }));
              obj.add(line);

              return obj;
            }
          case 'arrows':
            {
              // take inspiration from ArrowHelper, user cones and cylinders
              var _radius = object_json.radius || 1;
              var headLength = object_json.headLength || 2;
              var headWidth = object_json.headWidth || 2;

              // body
              var geom_cyl = new THREE.CylinderBufferGeometry(_radius * this.settings.cylinderScale, _radius * this.settings.cylinderScale, 1.0, this.settings.cylinderSegments);
              // head
              var geom_head = new THREE.ConeBufferGeometry(headWidth * this.settings.cylinderScale, headLength * this.settings.cylinderScale, this.settings.cylinderSegments);

              var _mat7 = this.makeMaterial(object_json.color);

              var _vec_y = new THREE.Vector3(0, 1, 0); // initial axis of cylinder
              var _quaternion2 = new THREE.Quaternion();
              var quaternion_head = new THREE.Quaternion();

              object_json.positionPairs.forEach(function (positionPair) {
                // the following is technically correct but could be optimized?

                var mesh = new THREE.Mesh(geom_cyl, _mat7);
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
                var mesh_head = new THREE.Mesh(geom_head, _mat7);
                mesh_head.position.set(vec_head.x, vec_head.y, vec_head.z);
                // rotate cylinder into correct orientation
                quaternion_head.setFromUnitVectors(_vec_y, vec_rel.normalize());
                mesh_head.setRotationFromQuaternion(quaternion_head);
                obj.add(mesh_head);
              });
              return obj;
            }
          case 'labels':
            {
              var label = document.createElement('div');
              label.className = 'tooltip';
              label.textContent = object_json.label;
              if (object_json.hoverLabel) {
                var hoverLabel = document.createElement('span');
                hoverLabel.textContent = object_json.hoverLabel;
                hoverLabel.className = 'tooltiptext';
                label.appendChild(hoverLabel);
              }
              var labelObject = new _CSS2DRenderer.CSS2DObject(label);
              obj.add(labelObject);
              return obj;
            }
          default:
            {
              return obj;
            }
        }
      }
    }, {
      key: 'makeMaterial',
      value: function makeMaterial(color, opacity) {
        var parameters = Object.assign(this.settings.material.parameters, {
          color: color || '#52afb0',
          opacity: opacity || 1.0
        });

        if (this.settings.renderer === "svg") {
          return new THREE.MeshBasicMaterial(parameters);
        }

        switch (this.settings.material.type) {
          case 'MeshStandardMaterial':
            {
              return new THREE.MeshStandardMaterial(parameters);
            }
          default:
            throw new Error('Unknown material.');
        }
      }
    }, {
      key: 'start',
      value: function start() {
        if (!this.frameId) {
          this.frameId = requestAnimationFrame(this.animate);
        }
      }
    }, {
      key: 'stop',
      value: function stop() {
        cancelAnimationFrame(this.frameId);
      }
    }, {
      key: 'animate',
      value: function animate() {
        this.renderScene();
        this.frameId = window.requestAnimationFrame(this.animate);
      }
    }, {
      key: 'renderScene',
      value: function renderScene() {
        this.renderer.render(this.scene, this.camera);
        this.labelRenderer.render(this.scene, this.camera);
      }
    }, {
      key: 'toggleVisibility',
      value: function toggleVisibility(namesToVisibility) {
        if (typeof namesToVisibility !== 'undefined') {
          for (var objName in namesToVisibility) {
            if (namesToVisibility.hasOwnProperty(objName)) {
              var obj = this.scene.getObjectByName(objName);
              if (typeof obj !== 'undefined') {
                obj.visible = Boolean(namesToVisibility[objName]);
              }
            }
          }
        }
        this.renderScene();
      }
    }, {
      key: 'getClickedReference',
      value: function getClickedReference(clientX, clientY) {
        var raycaster = new THREE.Raycaster();
        var mouse = new THREE.Vector2();

        mouse.x = clientX / this.renderer.domElement.clientWidth * 2 - 1;
        mouse.y = -(clientY / this.renderer.domElement.clientHeight) * 2 + 1;

        raycaster.setFromCamera(mouse, this.camera);

        // Three.js objects with click handlers we are interested in
        var intersects = raycaster.intersectObjects(this.clickable_objects);

        if (intersects.length > 0) {
          console.log('intersects', intersects[0].object.reference);
          return intersects[0].object.reference;
        }

        return null;
      }
    }], [{
      key: 'removeObjectByName',
      value: function removeObjectByName(scene, name) {
        // name is not necessarily unique, make this recursive ?
        var object = scene.getObjectByName(name);
        if (typeof object !== 'undefined') {
          scene.remove(object);
        }
      }
    }]);

    return Simple3DScene;
  }();

  exports.default = Simple3DScene;
});


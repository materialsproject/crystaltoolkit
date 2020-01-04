import React, {
  Component
} from 'react'
import PropTypes from 'prop-types'
import Simple3DScene from './Simple3DScene.js'

/**
 * Simple3DSceneComponent is intended to draw simple 3D scenes using the popular
 * Three.js scene graph library. In particular, the JSON representing the 3D scene
 * is intended to be human-readable, and easily generated via Python. In future, a
 * long-term approach would be to develop a library to generate Three.js JSON directly
 * inside Python to make this component redundant.
 */
export default class Simple3DSceneComponent extends Component {
  constructor (props) {
    super(props)
    this.handleClick = this.handleClick.bind(this) // Binding here
  }

  componentDidMount () {
    this.scene = new Simple3DScene(this.props.data, this.mount, this.props.settings)
    this.scene.toggleVisibility(this.props.toggleVisibility)
  }

  componentWillUpdate (nextProps, nextState) {
    if (nextProps.downloadRequest !== this.props.downloadRequest) {
      this.scene.download(nextProps.downloadRequest.filename, nextProps.downloadRequest.filetype)
    }

    if (nextProps.data !== this.props.data) {
      this.scene.addToScene(nextProps.data)
      this.scene.toggleVisibility(this.props.toggleVisibility)
    }

    if (nextProps.toggleVisibility !== this.props.toggleVisibility) {
      this.scene.toggleVisibility(nextProps.toggleVisibility)
    }
  }

  componentWillUnmount () {
    this.scene.stop()
    this.mount.removeChild(this.scene.renderer.domElement)
    this.scene.renderer.forceContextLoss()
    this.scene.renderer.context = null
    this.scene.renderer.domElement = null
    this.scene.renderer = null
  }

  handleClick (event) {
    event.preventDefault()

    var clickedReference = this.scene.getClickedReference(event.clientX, event.clientY)

    if (this.props.selectedObjectReference === clickedReference) {
      this.setState((state) => {
        return { selectedObjectCount: state.selectedObjectCount + 1 }
      })
    } else {
      this.setState({
        selectedObjectReference: clickedReference,
        selectedObjectCount: 1
      })
    }
  }

  render () {
    const {
      id
    } = this.props

    return (<div id={id}
      style={
        {
          width: '100%',
          height: '100%'
        }
      }
      ref={
        (mount) => {
          this.mount = mount
        }
      }
      onClick={this.handleClick}
    />
    )
  }
}

Simple3DSceneComponent.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks
   */
  id: PropTypes.string,

  /**
   * Simple3DScene JSON, the easiest way to generate this is to use the Scene class
   * in crystal_toolkit.core.scene and its to_json method.
   */
  data: PropTypes.object,

  /**
   * Options used for generating scene.
   * Supported options and their defaults are given as follows:
   * {
   *    antialias: true, // set to false to improve performance
   *    renderer: 'webgl', // 'svg' also an option, used for unit testing
   *    transparentBackground: false, // transparent background
   *    background: '#ffffff', // background color if not transparent,
   *    sphereSegments: 32, // decrease to improve performance
   *    cylinderSegments: 16, // decrease to improve performance
   *    staticScene: true, // disable if animation required
   *    defaultZoom: 0.8, // 1 will completely fill viewport with scen
   * }
   * There are several additional options used for debugging and testing,
   * please consult the source code directly for these.
   */
  settings: PropTypes.object,

  /**
   * Hide/show nodes in scene by its name (key), value is 1 to show the node
   * and 0 to hide it.
   */
  toggleVisibility: PropTypes.object,

  /**
   * Set to trigger a screenshot or scene download. Should be an object with
   * the structure:
   * {
   *    "n_requests": n_requests, // increment to trigger a new download request
   *    "filename": request_filename, // the download filename
   *    "filetype": "png", // the download format
   * }
   */
  downloadRequest: PropTypes.object,

  /**
   * Dash-assigned callback that should be called whenever any of the
   * properties change
   */
  setProps: PropTypes.func,

  /**
   * Reference to selected objects when clicked
   */
  selectedObjectReference: PropTypes.string,

  /**
   * Click count for selected object
   */
  selectedObjectCount: PropTypes.number

}

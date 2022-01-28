import { IRenderMime } from '@jupyterlab/rendermime-interfaces';
import { Widget } from '@lumino/widgets';
import { Scene } from '@materialsproject/mp-react-components';

/**
 * The default mime type for the extension.
 */
const MIME_TYPE = 'application/vnd.mp.ctk+json';

/**
 * The class name added to the extension.
 */
const CLASS_NAME = 'mimerenderer-mp_ctk_json';

/**
 * A widget for rendering Crystal Toolkit Scene JSON
 */
export class SceneRenderer extends Widget implements IRenderMime.IRenderer {
  private sceneContainer: HTMLDivElement;
  private model!: IRenderMime.IMimeModel;
  private scene: Scene;
  /**
   * Construct a new output widget
   */
  constructor(options: IRenderMime.IRendererOptions) {
    super();
    this.addClass(CLASS_NAME);
    this.sceneContainer = document.createElement('div') as HTMLDivElement;
    this.sceneContainer.setAttribute('style', 'height: 400px; width: 400px');
    this.node.appendChild(this.sceneContainer);
  }
  /**
   * Render Crystal Toolkit Scene JSON into this widget's node.
   */
  renderModel(model: IRenderMime.IMimeModel): Promise<void> {
    // Save reference to model
    this.model = model;

    // wait for the next event loop
    setTimeout(() => {
      this.scene = new Scene(
          model,  // sceneJSON
          this.sceneContainer,  // domElement
          {},  // settings
          50,  // size
          10, // padding
          (objects) => {  // clickCallback
                null
            },
          () => {  // cameraState
                /* we do not need to dispatch camera changes */
            }, null);
      this.scene.addToScene(this.model.data[MIME_TYPE]);
      this.scene.resizeRendererToDisplaySize();
    }, 0);

    return Promise.resolve();
  }

  dispose() {
    this.scene.onDestroy();
  }
}

/**
 * A mime renderer factory for Crystal Toolkit Scene JSON data.
 */
export const rendererFactory: IRenderMime.IRendererFactory = {
  safe: true,
  mimeTypes: [MIME_TYPE],
  createRenderer: (options) => new SceneRenderer(options),
};

/**
 * Extension definition.
 */
const extension: IRenderMime.IExtension = {
  id: 'crystaltoolkit-extension:plugin',
  rendererFactory,
  rank: 0,
  dataType: 'json',
  fileTypes: [
    {
      name: 'ctk_json',
      displayName: 'Crystal Toolkit Scene JSON',
      fileFormat: 'json',
      mimeTypes: [MIME_TYPE],
      extensions: ['.ctk.json'],
    },
  ],
  documentWidgetFactoryOptions: {
    name: 'SceneViewer',
    primaryFileType: 'ctk_json',
    fileTypes: ['ctk_json'],
    defaultFor: ['ctk_json'],
  },
};

export default extension;

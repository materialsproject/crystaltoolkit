import { IRenderMime } from '@jupyterlab/rendermime-interfaces';
import { Widget } from '@lumino/widgets';
/**
 * A widget for rendering Crystal Toolkit Scene JSON
 */
export declare class SceneRenderer extends Widget implements IRenderMime.IRenderer {
    private sceneContainer;
    private model;
    private scene;
    /**
     * Construct a new output widget
     */
    constructor(options: IRenderMime.IRendererOptions);
    /**
     * Render Crystal Toolkit Scene JSON into this widget's node.
     */
    renderModel(model: IRenderMime.IMimeModel): Promise<void>;
    dispose(): void;
}
/**
 * A mime renderer factory for Crystal Toolkit Scene JSON data.
 */
export declare const rendererFactory: IRenderMime.IRendererFactory;
/**
 * Extension definition.
 */
declare const extension: IRenderMime.IExtension;
export default extension;

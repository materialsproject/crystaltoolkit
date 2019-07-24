from abc import ABCMeta, abstractmethod

"""
This module defines the Renderable registry that is used to automatically
convert objects into Scenes for rendering
"""


class RenderableMeta(ABCMeta):

    all_instances = None

    def __init__(cls, name, bases, namespace, **kwds):
        """
        Initialize the Renderbale class
            1.) Find the namespace property for the target type
            2.) register in my main dict what
        """

        if name != "Renderable":
            if "target_type" not in namespace:
                raise Exception(
                    "Renderable pattern needs a target type"
                    "to associate this crystal_toolkit interfaces to"
                )
            if not any(b is Renderable for b in bases):
                raise Exception(
                    "Can only register Renderable"
                    "objects with the RenderableMeta type"
                )

            RenderableMeta.all_instances = RenderableMeta.all_instances or dict()

            RenderableMeta.all_instances[namespace["target_type"]] = cls

        super(RenderableMeta, cls).__init__(name, bases, namespace, **kwds)

    @classmethod
    def clear_interfaces(cls):
        RenderableMeta.all_instances = dict()

    @classmethod
    def get_interface(cls, obj):
        if type(obj) in RenderableMeta.all_instances:
            return RenderableMeta.all_instances[type(obj)]
        else:
            raise Exception(f"Could not find appropriate interface for {type(obj)}")


class Renderable(metaclass=RenderableMeta):
    @classmethod
    @abstractmethod
    def to_scene(cls, obj, **kwargs):
        raise NotImplemented("This method has not been implemented")

    @classmethod
    def render(cls, obj, **kwargs):
        return RenderableMeta.get_interface(obj).to_scene(cls, obj, **kwargs)

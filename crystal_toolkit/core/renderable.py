from abc import ABCMeta, abstractmethod

"""
This module defines the Renderable registry that is used to automatically
convert objects into Scenes for rendering
"""


class Renderer:

    all_interfaces = {}

    @staticmethod
    def register(rendering_type, render_method):
        Renderer.all_interfaces[rendering_type] = render_method

    @staticmethod
    def clear_interfaces():
        Renderer.all_interfaces = dict()

    @staticmethod
    def render(obj, *args, **kwargs):
        if type(obj) in Renderer.all_interfaces:
            return Renderer.all_interfaces[type(obj)](obj, *args, **kwargs)
        else:
            raise Exception(f"Could not find appropriate interface for {type(obj)}")

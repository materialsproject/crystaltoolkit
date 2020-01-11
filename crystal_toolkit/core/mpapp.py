from abc import ABC, abstractmethod
from crystal_toolkit.core.mpcomponent import MPComponent


class MPApp(MPComponent, ABC):
    """
    Class to make an app for the Materials Project website.
    """

    @property
    @abstractmethod
    def name(self):
        """
        Name of your app, will be included in navigation menu
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self):
        """
        Short description of app (max 140 characters).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def url(self):
        """
        URL of your app, will set its url as https://materialsproject.org/{url}
        """
        raise NotImplementedError

    def _sub_layouts(self):
        raise {}

    def generate_callbacks(self, app, cache):
        pass

    def get_layout(self, payload=None):
        """
        Return a Dash layout for the app. If the app requires any
        global set-up before a layout can be generated, put this in
        the app's initializer.

        :param payload: anything in the URL after
        https://materialsproject.org/your_app_name/
        """
        raise NotImplementedError

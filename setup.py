from setuptools import setup

exec (open('mp_dash_components/version.py').read())

setup(
    name='mp_dash_components',
    version=__version__,
    author='mkhorton',
    packages=['mp_dash_components'],
    include_package_data=True,
    license='MIT',
    description='Component for viewing crystallographic structures for the Materials Project.',
    install_requires=[]
)

from setuptools import setup

exec (open('mp_viewer/version.py').read())

setup(
    name='mp_viewer',
    version=__version__,
    author='mkhorton',
    packages=['mp_viewer'],
    include_package_data=True,
    license='MIT',
    description='Component for viewing crystallographic structures for the Materials Project.',
    install_requires=[]
)

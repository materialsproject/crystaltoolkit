from setuptools import setup, find_packages

exec (open('mp_dash_components/version.py').read())

setup(
    name='mp_dash_components',
    version=__version__,
    author='mkhorton',
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    description='Dash components for viewing Materials Project-specific objects '
                'such as crystallographic structures.',
    install_requires=["pymatgen>=2018.9.19", "dash>=0.26.4"]
)

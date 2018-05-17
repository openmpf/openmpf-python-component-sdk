import setuptools


setuptools.setup(
    name='PythonOcvComponent',
    version='0.1',
    packages=setuptools.find_packages(),
    install_requires=(
        'opencv-python>=3.3',
        'mpf_component_api>=0.1'
    ),
    entry_points={
        'mpf.exported_component': 'component = ocv_component.ocv_component:OcvComponent'
    }
)

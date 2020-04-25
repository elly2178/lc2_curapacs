from setuptools import setup

setup(
    name='provisioner',
    packages=['provisioner','routes'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)

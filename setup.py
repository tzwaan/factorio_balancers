from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='factorio_balancers',
    version='0.1',
    description='A property testing simulator for balancers from the game Factorio',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/tzwaan/factorio_balancers',
    author='Tijmen Zwaan',
    author_email='tijmen.zwaan@gmail.com',
    license='MIT',
    packages=['factorio_balancers'],
    install_requires=[
        'progress'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    scripts=[
        'bin/balancer_test'
    ],
    include_package_data=True,
    zip_safe=False)

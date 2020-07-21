from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='factorio_balancers',
    packages=['factorio_balancers'],
    version='0.2.2',
    license='MIT',
    description='A property testing simulator for balancers from the game Factorio',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Tijmen Zwaan',
    author_email='tijmen.zwaan@gmail.com',
    url='https://github.com/tzwaan/factorio_balancers',
    download_url='https://github.com/tzwaan/factorio_balancers/archive/v0.2.tar.gz',
    keywords=['factorio', 'balancer', 'blueprint'],
    install_requires=[
        'py_factorio_blueprints',
        'progress',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English'
    ],
    scripts=[
        'bin/balancer_test'
    ],
    include_package_data=True,
    zip_safe=False)

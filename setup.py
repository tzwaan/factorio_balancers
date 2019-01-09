from setuptools import setup

setup(name='factorio_balancers',
      version='0.1',
      description='A property testing simulator for balancers from the game Factorio',
      url='https://github.com/tzwaan/factorio_balancers',
      author='Tijmen Zwaan',
      author_email='tijmen.zwaan@gmail.com',
      license='MIT',
      packages=['factorio_balancers'],
      install_requires=[
          'progress'
      ],
      zip_safe=False)

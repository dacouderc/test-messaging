from setuptools import setup


setup(name='test-messaging',
      version='0.1',
      packages=['msgserver'],
      package_data={'msgserver': ['static/demo.*']},
      entry_points={
          'console_scripts': [
              'msgserver = msgserver.application:main'
          ]
      },
      install_requires=[
          'flask',
          'python-socketio',
          'eventlet',

          'mock',
          'pytest',
          'socketio-client',
      ])

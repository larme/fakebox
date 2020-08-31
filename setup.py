from setuptools import setup

setup(name='fakebox',
      version='0.1',
      description='toy dsp library in python',
      url='http://github.com/larme/fakebox',
      author='Zhao Shenyang',
      author_email='dev@zsy.im',
      license='MIT',
      packages=['fakebox'],
      install_requires=[
          'numpy>=1.0',
          'scipy>=1.0',
      ],
      zip_safe=False)

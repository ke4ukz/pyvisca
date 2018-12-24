from setuptools import setup

def readme():
	with open('README.me') as f:
		return f.read()

setup(name='pyvisca',
	  version='0.1',
	  description='RS-232 VISCA camera control package',
	  url='https://github.com/ke4ukz/pyvisca',
	  author='Jonathan Dean',
	  author_email='ke4ukz@gmx.com',
	  license='GNU GPL v3',
	  packages=['pyvisca'],
	  install_requires=[
		  'pyserial'
	  ],
	  zip_safe=False)
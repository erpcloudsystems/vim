from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in vim/__init__.py
from vim import __version__ as version

setup(
	name="vim",
	version=version,
	description="customization",
	author="ecs",
	author_email="info@erpcloud.systems",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

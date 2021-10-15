
import setuptools

from mrd.storage import version

setuptools.setup(
    name="mrd.storage",
    version=version,
    author="",
    author_email="",
    description="",
    license="",
    url="",
    packages=setuptools.find_packages(where='mrd'),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Medical Science Apps.'
    ],
    python_requires='>=3.6',
    install_requires=[
        'gunicorn',
        'flask',
        'flask-restful',
        'sqlalchemy'
    ]
)

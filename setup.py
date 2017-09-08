from setuptools import setup

test_requires = [
    'pytest',
]

setup(
    name = 'trusona-pizza-client',
    #py_modules = ['app'],
    packages = ['pizza_client'],
    entry_points = {
        'console_scripts': ['pizza-client=pizza_client.app:main'],
    },
    version = '0.0.1',
    description = (
        'An implimentation of the Trusona pizza client'
    ),
    author = 'Daniel Wozniak',
#    description_file = 'README.md',
    author_email = 'dan@woz.io',
    url = 'https://github.com/dwoz/trusona-pizza-client',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
)

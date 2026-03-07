from setuptools import setup, find_packages
setup(
    name='codex-loop',
    version='2.1.0',
    packages=find_packages(),
    install_requires=['requests'],
    entry_points={
        'console_scripts': [
            'codex-loop=scripts.codex_loop_brain:main',
        ],
    },
)

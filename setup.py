from setuptools import setup, find_packages


def readme():
    return open("README.md").read()


if __name__ == "__main__":
    setup(
        name="timeloopfe",
        version="0.4",
        description="Front End for Timeloop & Accelergy",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        ],
        keywords="accelerator hardware energy estimation",
        author="Tanner Andrulis",
        author_email="andurlis@mit.edu",
        license="MIT",
        packages=find_packages(),
        install_requires=[
            "accelergy >= 0.4",
            "ruamel.yaml",
            "psutil",
            "joblib",
            "argparse",
        ],
        python_requires=">=3.8",
        # Have the "timeloop" or "tl" commands call timeloopfe/command_line_interface.py
        entry_points={
            "console_scripts": [
                "timeloop = timeloopfe.command_line_interface:main",
                "tl = timeloopfe.command_line_interface:main",
            ],
        },
    )

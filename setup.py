from setuptools import setup, Extension
import pybind11
import numpy

ffmpeg_dir = r"C:\ffmpeg"  

module = Extension(
    'libh264decoder',
    sources=['h264decoder_python.cpp', 'h264decoder.cpp'],
    include_dirs=[
        pybind11.get_include(),
        numpy.get_include(),
        ffmpeg_dir + r"\include"
    ],
    library_dirs=[
        ffmpeg_dir + r"\lib"
    ],
    libraries=[
        'avcodec', 'avformat', 'avutil', 'swscale'
    ],
    define_macros=[
        ('WIN32_LEAN_AND_MEAN', None),
        ('NOMINMAX', None),
    ],
    extra_compile_args=['/EHsc', '/std:c++17'],
    language='c++'
)

setup(
    name='libh264decoder',
    version='1.0',
    ext_modules=[module]
)
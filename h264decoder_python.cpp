#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

#include "h264decoder.hpp"

namespace py = pybind11;
using ubyte = unsigned char;

// Python-exposed wrapper class
class PyH264Decoder
{
  H264Decoder decoder;
  ConverterRGB24 converter;

public:
  py::tuple decode_frame(const py::bytes &data_in_str);
  py::list decode(const py::bytes &data_in_str);

private:
  py::tuple decode_frame_impl(const ubyte *data_in, ssize_t len,
                              ssize_t &num_consumed,
                              bool &is_frame_available);
};

py::tuple PyH264Decoder::decode_frame_impl(const ubyte *data_in, ssize_t len,
                                           ssize_t &num_consumed,
                                           bool &is_frame_available)
{
  // Release GIL for potentially long-running operation
  py::gil_scoped_release release;

  num_consumed = decoder.parse_data((ubyte *)data_in, len);

  if (is_frame_available = decoder.is_frame_available())
  {
    const auto &frame = decoder.decode_frame();
    int w, h;
    std::tie(w, h) = width_height(frame);
    Py_ssize_t out_size = converter.predict_size(w, h);

    // Reacquire GIL for Python operations
    py::gil_scoped_acquire acquire;

    py::bytes py_out_str(nullptr, out_size);
    char *out_buffer = PyBytes_AsString(py_out_str.ptr());

    // Release GIL again for conversion
    py::gil_scoped_release release2;
    const auto &rgbframe = converter.convert(frame, (ubyte *)out_buffer);

    // Reacquire GIL for return
    py::gil_scoped_acquire acquire2;
    return py::make_tuple(py_out_str, w, h, row_size(rgbframe));
  }
  else
  {
    py::gil_scoped_acquire acquire;
    return py::make_tuple(py::none(), 0, 0, 0);
  }
}

py::tuple PyH264Decoder::decode_frame(const py::bytes &data_in_str)
{
  ssize_t len = PyBytes_Size(data_in_str.ptr());
  const ubyte *data_in = (const ubyte *)(PyBytes_AsString(data_in_str.ptr()));

  ssize_t num_consumed = 0;
  bool is_frame_available = false;
  auto frame = decode_frame_impl(data_in, len, num_consumed, is_frame_available);

  return py::make_tuple(frame, num_consumed);
}

py::list PyH264Decoder::decode(const py::bytes &data_in_str)
{
  ssize_t len = PyBytes_Size(data_in_str.ptr());
  const ubyte *data_in = (const ubyte *)(PyBytes_AsString(data_in_str.ptr()));

  py::list out;

  try
  {
    while (len > 0)
    {
      ssize_t num_consumed = 0;
      bool is_frame_available = false;

      try
      {
        auto frame = decode_frame_impl(data_in, len, num_consumed, is_frame_available);
        if (is_frame_available)
        {
          out.append(frame);
        }
      }
      catch (const H264DecodeFailure &e)
      {
        if (num_consumed <= 0)
          throw e;
      }

      len -= num_consumed;
      data_in += num_consumed;
    }
  }
  catch (const H264DecodeFailure &)
  {
  }

  return out;
}

PYBIND11_MODULE(libh264decoder, m)
{
  m.doc() = "H.264 decoder module using FFmpeg";

  py::class_<PyH264Decoder>(m, "H264Decoder")
      .def(py::init<>())
      .def("decode_frame", &PyH264Decoder::decode_frame, "Decode a single frame")
      .def("decode", &PyH264Decoder::decode, "Decode all frames from data");

  m.def("disable_logging", &disable_logging, "Disable FFmpeg logging");
}
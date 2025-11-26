#pragma once

// Prevent Windows from defining problematic macros
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

#ifndef NOMINMAX
#define NOMINMAX
#endif

/*
This h264 decoder class is just a thin wrapper around libav
functions to decode h264 videos.
*/

#include <cstdlib>
#include <stdexcept>
#include <utility>

// For ssize_t
#ifdef _MSC_VER
#include <BaseTsd.h>
typedef SSIZE_T ssize_t;
#else
#include <sys/types.h>
#endif

// Forward declarations
struct AVCodecContext;
struct AVFrame;
struct AVCodec;
struct AVCodecParserContext;
struct SwsContext;
struct AVPacket;

// Exception hierarchy
class H264Exception : public std::runtime_error
{
public:
  explicit H264Exception(const char *s) : std::runtime_error(s) {}
};

class H264InitFailure : public H264Exception
{
public:
  explicit H264InitFailure(const char *s) : H264Exception(s) {}
};

class H264DecodeFailure : public H264Exception
{
public:
  explicit H264DecodeFailure(const char *s) : H264Exception(s) {}
};

// Decoder class
class H264Decoder
{
  AVCodecContext *context;
  AVFrame *frame;
  AVCodec *codec;
  AVCodecParserContext *parser;
  AVPacket *pkt;

public:
  H264Decoder();
  ~H264Decoder();

  ssize_t parse_data(const unsigned char *in_data, ssize_t in_size);
  bool is_frame_available() const;
  const AVFrame &decode_frame();
};

// Converter class
class ConverterRGB24
{
  SwsContext *context;
  AVFrame *framergb;

public:
  ConverterRGB24();
  ~ConverterRGB24();

  int predict_size(int w, int h);
  const AVFrame &convert(const AVFrame &frame, unsigned char *out_rgb);
};

// Utility helpers
void disable_logging();
std::pair<int, int> width_height(const AVFrame &);
int row_size(const AVFrame &);
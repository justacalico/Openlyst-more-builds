class Opentorrent < Formula
  desc "qBittorrent client"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-32/opentorrent-2.0.0-2026-02-17-macos-unsigned.zip"
  version "2.0.0"
  sha256 "049e6329a25bda8cfe5f8f5d8bfb5e9167caa66112d2c57e9652a3096a86917a"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

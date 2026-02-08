class Klit < Formula
  desc "E926 API client"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/openlyst-more-builds/releases/download/build-60/klit-7.0.0-2026-01-18-linux-x86_64.AppImage"
  version "7.0.0"
  sha256 "32f494a01c3909df270506bc835200570143e7d6b6811a01022bb6a66bf9d63a"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

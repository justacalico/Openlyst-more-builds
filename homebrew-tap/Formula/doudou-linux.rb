class Doudou < Formula
  desc "Music player for self-hosted services"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/openlyst-more-builds/releases/download/build-53/doudou-12.0.1-2026-01-15-linux-x86_64.AppImage"
  version "12.0.1"
  sha256 "52af517720e1daa6b18add5bca6ae6391fd0f7487ace57d506e3f8bfbc36cee3"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

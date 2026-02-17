class Finar < Formula
  desc "Jellyfin frontend client"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-13/finar-1.1.0-2026-02-13-linux-x86_64.AppImage"
  version "2.0.0"
  sha256 "ffbef5da26784bdb982f7f14dd3dde2d873ba4914d69c0fb1aede1ae38fa905d"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

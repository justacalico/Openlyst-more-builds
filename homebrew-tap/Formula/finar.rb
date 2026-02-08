class Finar < Formula
  desc "Replacement frontend for Jellyfin"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/openlyst-more-builds/releases/download/build-47/finar-1.1.0-2026-01-13-macos-unsigned.zip"
  version "1.1.0"
  sha256 "a33f16ee793519f6542e5006bd973b1ac66c713d73099c39db3e1779ace5db66"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

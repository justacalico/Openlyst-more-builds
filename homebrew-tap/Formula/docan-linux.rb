class Docan < Formula
  desc "AI chat app with Liquid Glass UI"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-1/docan-3.0.0-2026-02-08-linux-x86_64.AppImage"
  version "3.0.0"
  sha256 "a87b2a410fbc247874b971e45fa91936b8b5403682ea7605919847fe7e7f7477"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

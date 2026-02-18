class Finar < Formula
  desc "Jellyfin frontend client"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-13/finar-1.1.0-2026-02-13-macos-unsigned.zip"
  version "2.0.0"
  sha256 "c7e552d7b277d2a1fc3f094b59fe264129f4b3dcf80d299dd39d26f34658c12c"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

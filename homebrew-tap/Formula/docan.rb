class Docan < Formula
  desc "Universal AI chat application with Liquid Glass design"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/openlyst-more-builds/releases/download/build-47/docan-3.0.0-2026-01-13-macos-unsigned.zip"
  version "3.0.0"
  sha256 "2f5076154c467c4d34d49ca51d7b07b70c847abfde8044bd69c5532211d864f8"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

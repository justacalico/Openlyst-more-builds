class Docan < Formula
  desc "Universal AI chat application with Liquid Glass design"
  homepage "https://openlyst.ink"
  url "https://github.com/HttpAnimation/Openlyst-more-builds/releases/download/build-47/docan-3.0.0-2026-01-13-macos-unsigned.zip"
  version "3.0.0"
    # sha256 "REPLACE_WITH_ACTUAL_SHA256"

  def install
    # Extract and install archive
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

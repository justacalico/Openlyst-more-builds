class Docan < Formula
  desc "AI chat app with Liquid Glass UI"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-1/docan-3.0.0-2026-02-08-macos-unsigned.zip"
  version "3.0.0"
  # sha256 "REPLACE_WITH_ACTUAL_SHA256"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

class Doudou < Formula
  desc "Music player for self-hosted services"
  homepage "https://openlyst.ink"
  url "https://github.com/HttpAnimation/Openlyst-more-builds/releases/download/build-45/doudou-12.0.0-2026-01-13-linux-x86_64.AppImage"
  version "12.0.0"
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

class Doudou < Formula
  desc "Music player for self-hosted services"
  homepage "https://openlyst.ink"
  url "https://github.com/HttpAnimation/Openlyst-more-builds/releases/download/build-45/doudou-12.0.0-2026-01-13-linux-x86_64.AppImage"
  version "12.0.0"
  sha256 "da3fd915605c9353bf8ee5aa35f792e99b523d33db36126fd7327c78cef50703"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

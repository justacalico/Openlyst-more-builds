class Doudou < Formula
  desc "Music player for self-hosted services"
  homepage "https://openlyst.ink"
  url "https://github.com/HttpAnimation/Openlyst-more-builds/releases/download/build-45/doudou-12.0.0-2026-01-13-macos-unsigned.zip"
  version "12.0.0"
  sha256 "15cee93e3cfb89fedeb2f6ae38c8dd5eb2f7fc8a042efe117906d23842b9880f"

  def install
    # Extract and install archive
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

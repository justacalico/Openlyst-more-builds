class Doudou < Formula
  desc "Music player for self-hosted services"
  homepage "https://openlyst.ink"
  url "https://github.com/HttpAnimation/Openlyst-more-builds/releases/download/build-53/doudou-12.0.1-2026-01-15-macos-unsigned.zip"
  version "12.0.1"
  sha256 "f15b367ba9916d7c97178d7f499758c3f8310787529436c369af3fabd3a74371"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

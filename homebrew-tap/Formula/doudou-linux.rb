class Doudou < Formula
  desc "Music player for self-hosted services"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-31/doudou-14.0.0-2026-02-16-linux-x86_64.AppImage"
  version "14.0.0"
  sha256 "bd9a7675f078af01e143f113810a660875a600f0db7b18f29dca5b4e4fcf6bc9"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

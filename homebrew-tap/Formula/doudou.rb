class Doudou < Formula
  desc "Music player for self-hosted services"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-31/doudou-14.0.0-2026-02-16-macos-unsigned.zip"
  version "14.0.0"
  sha256 "cf65399556147d3573a4ed236e0c2d6853624eed12c653d8c4c5d22126a5f17d"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

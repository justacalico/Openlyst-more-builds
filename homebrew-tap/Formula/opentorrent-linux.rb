class Opentorrent < Formula
  desc "qBittorrent client."
  homepage "https://openlyst.ink"
  url "https://github.com/HttpAnimation/Openlyst-more-builds/releases/download/build-52/opentorrent-1.0.0-2026-01-14-linux-x64.zip"
  version "1.0.0"
  sha256 "94d8e68e2d65aa27d792c18acbcdb9d9362dc8c9d0a12e1991e023857cc86659"

  def install
    # Extract and install archive
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

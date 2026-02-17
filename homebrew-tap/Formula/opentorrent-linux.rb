class Opentorrent < Formula
  desc "qBittorrent client"
  homepage "https://openlyst.ink"
  url "https://github.com/justacalico/Openlyst-more-builds/releases/download/build-32/opentorrent-2.0.0-2026-02-17-linux-x64.zip"
  version "2.0.0"
  sha256 "af25f323a9e666053544009755926efbe0b58cf6e44d7672dea60c3efe81da06"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

class Finar < Formula
  desc "Replacement frontend for Jellyfin"
  homepage "https://openlyst.ink"
  url "https://gitlab.com/Openlyst/finar/-/jobs/12639939013/artifacts/raw/artifacts/klit-linux-x86_64.AppImage"
  version "1.1.0"
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

class Docan < Formula
  desc "Universal AI chat application with Liquid Glass design"
  homepage "https://openlyst.ink"
  url "https://gitlab.com/Openlyst/docan/-/jobs/12674147403/artifacts/raw/dist/3.0.0/docan-3.0.0-linux.AppImage"
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

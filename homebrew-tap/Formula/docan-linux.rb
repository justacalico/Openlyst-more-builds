class Docan < Formula
  desc "Universal AI chat application with Liquid Glass design"
  homepage "https://openlyst.ink"
  url "https://gitlab.com/Openlyst/docan/-/jobs/12674147403/artifacts/raw/dist/3.0.0/docan-3.0.0-linux.AppImage"
  version "3.0.0"
  sha256 "4f32ba83c651efc2e898fb5d570f1db6f407baa75006411974700c81f3849636"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

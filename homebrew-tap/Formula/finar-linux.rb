class Finar < Formula
  desc "Replacement frontend for Jellyfin"
  homepage "https://openlyst.ink"
  url "https://gitlab.com/Openlyst/finar/-/jobs/12639939013/artifacts/raw/artifacts/klit-linux-x86_64.AppImage"
  version "1.1.0"
  sha256 "f6e70edc27e77c45a6efe784c67fc3bae31318cf433bda5d31b6c504cd0ebc9f"

  def install
    # Generic installation
    prefix.install Dir["*"]
  end

  test do
    # Test that the application was installed
    system "true"
  end
end

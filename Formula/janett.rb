class Janett < Formula
  include Language::Python::Virtualenv

  desc "Interactive tutorial generator powered by local LLMs or OpenAI"
  homepage "https://github.com/janettai/janett.chat"
  url "https://files.pythonhosted.org/packages/source/j/janett/janett-0.2.0.tar.gz"
  sha256 "REPLACE_AFTER_PYPI_PUBLISH"
  license "MIT"
  head "https://github.com/janettai/janett.chat.git", branch: "main"

  depends_on "python@3.12"

  def install
    virtualenv_create(libexec, "python3.12")
    system libexec/"bin/pip", "install", "janett==#{version}"
    bin.install_symlink libexec/"bin/janett"
  end

  def caveats
    <<~EOS
      Janett works best with Ollama for free, local AI:

        brew install ollama
        ollama pull llama3.2
        ollama serve

      Then run: janett

      Or use OpenAI by setting your API key in the app with /apikey
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/janett --version 2>&1")
  end
end
